import json
import time
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, asc, desc
from fastapi import HTTPException
from app.db.models import Product
from app.core.config import settings
from app.core.redis import redis_client
from app.elasticsearch.client import es_client

logger = logging.getLogger(__name__)



class ProductService:
    @staticmethod
    def _generate_cache_key(
        prefix: str,
        page: int,
        size: int,
        query: Optional[str] = None,
        category: Optional[str] = None,
        sort_by: str = "id",
        sort_order: str = "asc",
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
    ) -> str:
        """
        CONCEPT: DYNAMIC CACHE KEY
        Generates a unique key based on EVERY parameter. This prevents "Cache Pollution"
        where a filtered request accidentally returns non-filtered cached data.
        """
        parts = [prefix, f"p{page}", f"s{size}"]
        if query: parts.append(f"q:{query}")
        if category: parts.append(f"c:{category}")
        parts.append(f"sb:{sort_by}")
        parts.append(f"so:{sort_order}")
        
        # Add dynamic filters to the key
        if min_price is not None: parts.append(f"minp:{min_price}")
        if max_price is not None: parts.append(f"maxp:{max_price}")
        if min_rating is not None: parts.append(f"minr:{min_rating}")
        
        return ":".join(parts)

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
    async def get_products(
        db: Session,
        page: int = 1,
        size: int = 10,
        category: Optional[str] = None,
        sort_by: str = "id",
        sort_order: str = "asc",
    ):
        """
        ### 📋 MySQL PRODUCT LISTING
        Retrieves a paginated list of products from the relational database.

        **WHY**: This is the 'Source of Truth' path. It is used for browsing categories 
                 and viewing the general catalog without a search query.
        
        **WHEN USEFUL**: 
        - Building a category-based landing page.
        - Sorting the entire catalog by Price or Rating.

        **PERFORMANCE**: Implements Redis Caching with dynamic keys.
        
        **EXAMPLE**: `p=2, size=20, category='beauty'` -> Fetches 2nd page of beauty items.
        """
        cache_key = ProductService._generate_cache_key(
            "list", page, size, None, category, sort_by, sort_order
        )

        try:
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                logger.info("CACHE HIT | Listing: %s", cache_key)
                return json.loads(cached_data)
        except Exception as e:
            logger.warning("CACHE ERROR | %s", e)

        # SQL Logic
        offset = (page - 1) * size
        base_stmt = select(Product)
        count_stmt = select(func.count()).select_from(Product)

        if category:
            base_stmt = base_stmt.where(Product.category == category)
            count_stmt = count_stmt.where(Product.category == category)

        sort_column_map = {"id": Product.id, "price": Product.price, "title": Product.title, "rating": Product.rating, "stock": Product.stock}
        sort_column = sort_column_map.get(sort_by, Product.id)
        ordering = asc(sort_column) if sort_order.lower() == "asc" else desc(sort_column)

        t0 = time.perf_counter()
        items = db.scalars(base_stmt.order_by(ordering).offset(offset).limit(size)).all()
        total = db.scalar(count_stmt) or 0
        took_ms = round((time.perf_counter() - t0) * 1000, 2)

        result = {
            "total": total, "page": page, "size": size, 
            "items": [item.to_dict() for item in items], 
            "took_ms": took_ms, "cached": False
        }

        try:
            cache_result = result.copy()
            cache_result["cached"] = True
            await redis_client.set(cache_key, json.dumps(cache_result), ex=300)
        except Exception as e:
            logger.warning("CACHE STORE ERROR | %s", e)

        return result

    @staticmethod
    async def search_products(
        query: str,
        page: int = 1,
        size: int = 10,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
    ):
        """
        ### 🔍 ELASTICSEARCH FULL-TEXT SEARCH
        Performs advanced search using the Elasticsearch engine.

        **WHY**: MySQL `LIKE` queries are slow and lack relevance. Elasticsearch provides 
                 Boosting, Fuzziness, and Synonyms for a premium user experience.
        
        **WHEN USEFUL**: 
        - Handling typos (e.g., 'liptick' -> 'lipstick').
        - Mapping synonyms (e.g., 'perfume' -> 'fragrance').
        - Ranking results based on relevance score.

        **SCALABILITY**: Sharded across multiple nodes for high-speed concurrent searching.
        
        **EXAMPLE**: `query='laptp', min_p=500` -> Typos corrected, results filtered by price.
        """
        # --- CACHE LOGIC: CHECKING REDIS ---
        cache_key = ProductService._generate_cache_key(
            "search", page, size, query, category, "score", "desc", min_price, max_price, min_rating
        )
        logger.info("SEARCH | Query: '%s' | Generating Cache Key: %s", query, cache_key)

        try:
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                logger.info("CACHE HIT | Served from Redis: %s", cache_key)
                return json.loads(cached_data)
        except Exception as e:
            logger.error("CACHE ERROR | Redis link failed: %s", e)

        # --- ES LOGIC: APPLYING ADVANCED FEATURES ---
        logger.info("SEARCH | Applying Fuzziness (AUTO) & Synonyms for: '%s'", query)
        from_ = (page - 1) * size
        must_clause = [{"multi_match": {"query": query, "fields": ["title^3", "description^2", "brand^2", "tags", "category"], "fuzziness": "AUTO"}}]
        filter_clause = []
        if category: filter_clause.append({"term": {"category": category}})
        if min_price is not None or max_price is not None:
            pr = {}
            if min_price is not None: pr["gte"] = min_price
            if max_price is not None: pr["lte"] = max_price
            filter_clause.append({"range": {"price": pr}})
        if min_rating is not None: filter_clause.append({"range": {"rating": {"gte": min_rating}}})

        body = {
            "from": from_, "size": size,
            "query": {"bool": {"must": must_clause, "filter": filter_clause}},
            "sort": [{"_score": {"order": "desc"}}, {"rating": {"order": "desc", "missing": "_last"}}],
            "aggs": {"categories": {"terms": {"field": "category", "size": 20}}, "brands": {"terms": {"field": "brand", "size": 20}}},
        }

        t0 = time.perf_counter()
        response = es_client.search(index=settings.ELASTICSEARCH_INDEX, body=body)
        took_ms = round((time.perf_counter() - t0) * 1000, 2)
        es_took_ms = response.get("took")

        hits = response["hits"]["hits"]
        total = response["hits"]["total"]["value"]
        items = [hit["_source"] for hit in hits]
        shards_info = response.get("_shards", {})

        logger.info(
            "SEARCH SUCCESS | Query: '%s' | Total Found: %d | Time: %sms | Shards Hit: %d/%d",
            query, total, took_ms, shards_info.get("successful"), shards_info.get("total")
        )

        aggs_raw = response.get("aggregations", {})
        aggregations = {
            "categories": [{"key": b["key"], "doc_count": b["doc_count"]} for b in aggs_raw.get("categories", {}).get("buckets", [])],
            "brands": [{"key": b["key"], "doc_count": b["doc_count"]} for b in aggs_raw.get("brands", {}).get("buckets", [])],
        }

        result = {
            "total": total, "page": page, "size": size, "items": items, "aggregations": aggregations,
            "took_ms": took_ms, "es_took_ms": es_took_ms,
            "shard_info": {"total": shards_info.get("total"), "successful": shards_info.get("successful")},
            "cached": False
        }

        try:
            cache_result = result.copy()
            cache_result["cached"] = True
            await redis_client.set(cache_key, json.dumps(cache_result), ex=300)
        except Exception as e:
            logger.warning("CACHE STORE ERROR | %s", e)

        return result
