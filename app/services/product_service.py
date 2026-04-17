from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, asc, desc
from fastapi import HTTPException
from app.db.models import Product
from app.core.config import settings
from app.elasticsearch.client import es_client


class ProductService:
    @staticmethod
    def get_categories(db: Session) -> list[str]:
        stmt = select(Product.category).distinct().order_by(Product.category.asc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_product_by_id(db: Session, product_id: int) -> dict:
        product = db.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product.to_dict()

    @staticmethod
    def get_products(
        db: Session,
        page: int = 1,
        size: int = 10,
        category: Optional[str] = None,
        sort_by: str = "id",
        sort_order: str = "asc",
    ):
        offset = (page - 1) * size

        base_stmt = select(Product)
        count_stmt = select(func.count()).select_from(Product)

        if category:
            base_stmt = base_stmt.where(Product.category == category)
            count_stmt = count_stmt.where(Product.category == category)

        sort_column_map = {
            "id": Product.id,
            "price": Product.price,
            "title": Product.title,
            "rating": Product.rating,
            "stock": Product.stock,
        }
        sort_column = sort_column_map.get(sort_by, Product.id)
        ordering = asc(sort_column) if sort_order.lower() == "asc" else desc(sort_column)

        items = db.scalars(base_stmt.order_by(ordering).offset(offset).limit(size)).all()
        total = db.scalar(count_stmt) or 0

        return {"total": total, "page": page, "size": size, "items": [item.to_dict() for item in items]}

    @staticmethod
    def search_products(
        query: str,
        page: int = 1,
        size: int = 10,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
    ):
        from_ = (page - 1) * size

        # Build the must clause with boosted multi_match
        must_clause = [
            {
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "description^2", "brand^2", "tags", "category"],
                    "fuzziness": "AUTO",
                }
            }
        ]

        # Build filter clauses dynamically
        filter_clause = []
        if category:
            filter_clause.append({"term": {"category": category}})
        if min_price is not None or max_price is not None:
            price_range = {}
            if min_price is not None:
                price_range["gte"] = min_price
            if max_price is not None:
                price_range["lte"] = max_price
            filter_clause.append({"range": {"price": price_range}})
        if min_rating is not None:
            filter_clause.append({"range": {"rating": {"gte": min_rating}}})

        body = {
            "from": from_,
            "size": size,
            "query": {
                "bool": {
                    "must": must_clause,
                    "filter": filter_clause,
                }
            },
            "sort": [
                {"_score": {"order": "desc"}},
                {"rating": {"order": "desc", "missing": "_last"}},
            ],
            # Aggregations for faceted search
            "aggs": {
                "categories": {
                    "terms": {"field": "category", "size": 20}
                },
                "brands": {
                    "terms": {"field": "brand", "size": 20}
                },
            },
        }

        response = es_client.search(index=settings.ELASTICSEARCH_INDEX, body=body)

        hits = response["hits"]["hits"]
        total = response["hits"]["total"]["value"]
        items = [hit["_source"] for hit in hits]

        # Extract aggregation buckets
        aggs_raw = response.get("aggregations", {})
        aggregations = {
            "categories": [
                {"key": b["key"], "doc_count": b["doc_count"]}
                for b in aggs_raw.get("categories", {}).get("buckets", [])
            ],
            "brands": [
                {"key": b["key"], "doc_count": b["doc_count"]}
                for b in aggs_raw.get("brands", {}).get("buckets", [])
            ],
        }

        return {
            "total": total,
            "page": page,
            "size": size,
            "items": items,
            "aggregations": aggregations,
        }