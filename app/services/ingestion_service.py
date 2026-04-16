import logging
import requests
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.core.config import settings
from app.db.models import Product
from app.elasticsearch.client import es_client
from app.elasticsearch.index_manager import create_products_index

logger = logging.getLogger(__name__)


class IngestionService:
    @staticmethod
    def fetch_products_from_source() -> list[dict]:
        logger.info("Fetching products from external source: %s", settings.DUMMY_PRODUCTS_URL)
        response = requests.get(settings.DUMMY_PRODUCTS_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("products", [])

    @staticmethod
    def bootstrap_data(db: Session) -> None:
        product_count = db.scalar(select(func.count()).select_from(Product)) or 0
        create_products_index()

        if product_count > 0:
            logger.info("Products already exist in MySQL. Skipping DB ingestion.")
            es_count = es_client.count(index=settings.ELASTICSEARCH_INDEX)["count"]
            if es_count == 0:
                logger.info("Elasticsearch index empty. Re-indexing from MySQL.")
                IngestionService.index_all_from_db(db)
            return

        products = IngestionService.fetch_products_from_source()
        logger.info("Fetched %s products", len(products))

        db_products = []
        for item in products:
            product = Product(
                id=item["id"],
                title=item.get("title", ""),
                description=item.get("description", ""),
                category=item.get("category", ""),
                brand=item.get("brand"),
                sku=item.get("sku"),
                price=item.get("price", 0),
                discount_percentage=item.get("discountPercentage"),
                rating=item.get("rating"),
                stock=item.get("stock"),
                thumbnail=item.get("thumbnail"),
            )
            db_products.append(product)

        db.add_all(db_products)
        db.commit()
        logger.info("Inserted %s products into MySQL", len(db_products))

        IngestionService.index_documents(products)

    @staticmethod
    def index_documents(products: list[dict]) -> None:
        actions = []
        for item in products:
            doc = {
                "id": item["id"],
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "category": item.get("category", ""),
                "brand": item.get("brand"),
                "sku": item.get("sku"),
                "price": item.get("price", 0),
                "discount_percentage": item.get("discountPercentage"),
                "rating": item.get("rating"),
                "stock": item.get("stock"),
                "thumbnail": item.get("thumbnail"),
            }
            actions.append({"index": {"_index": settings.ELASTICSEARCH_INDEX, "_id": item["id"]}})
            actions.append(doc)

        if actions:
            es_client.bulk(operations=actions, refresh=True)
            logger.info("Indexed %s products into Elasticsearch", len(products))

    @staticmethod
    def index_all_from_db(db: Session) -> None:
        products = db.scalars(select(Product)).all()
        payload = [p.to_dict() for p in products]

        actions = []
        for item in payload:
            actions.append({"index": {"_index": settings.ELASTICSEARCH_INDEX, "_id": item["id"]}})
            actions.append(item)

        if actions:
            es_client.bulk(operations=actions, refresh=True)
            logger.info("Re-indexed %s products from MySQL into Elasticsearch", len(payload))