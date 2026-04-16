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
    def get_product_by_id(db: Session, product_id: int) -> Product:
        product = db.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product

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

        return {"total": total, "page": page, "size": size, "items": items}

    @staticmethod
    def search_products(
        query: str,
        page: int = 1,
        size: int = 10,
        category: Optional[str] = None,
    ):
        from_ = (page - 1) * size

        must_clause = [
            {
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "description^2", "brand", "category"],
                    "fuzziness": "AUTO",
                }
            }
        ]

        filter_clause = []
        if category:
            filter_clause.append({"term": {"category": category}})

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
                {"id": {"order": "asc"}}
            ],
        }

        response = es_client.search(index=settings.ELASTICSEARCH_INDEX, body=body)

        hits = response["hits"]["hits"]
        total = response["hits"]["total"]["value"]

        items = [hit["_source"] for hit in hits]

        return {"total": total, "page": page, "size": size, "items": items}