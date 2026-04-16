import logging
import requests
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.core.config import settings
from app.db.models import Product, ProductTag, ProductImage, Review
from app.elasticsearch.client import es_client
from app.elasticsearch.index_manager import create_products_index

logger = logging.getLogger(__name__)

def parse_iso_datetime(date_str: str) -> datetime | None:
    if not date_str:
        return None
    try:
        # Handling the Z suffix common in JSON (e.g. from dummyjson)
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        logger.warning(f"Could not parse date string: {date_str}")
        return None

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
            # Build Product
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
                weight=item.get("weight"),
                warranty_information=item.get("warrantyInformation"),
                shipping_information=item.get("shippingInformation"),
                availability_status=item.get("availabilityStatus"),
                return_policy=item.get("returnPolicy"),
                minimum_order_quantity=item.get("minimumOrderQuantity"),
            )

            # Dimensions
            dimensions = item.get("dimensions", {})
            if dimensions:
                product.dimension_width = dimensions.get("width")
                product.dimension_height = dimensions.get("height")
                product.dimension_depth = dimensions.get("depth")

            # Meta
            meta_data = item.get("meta", {})
            if meta_data:
                product.meta_created_at = parse_iso_datetime(meta_data.get("createdAt"))
                product.meta_updated_at = parse_iso_datetime(meta_data.get("updatedAt"))
                product.meta_barcode = meta_data.get("barcode")
                product.meta_qr_code = meta_data.get("qrCode")

            # Tags
            for t in item.get("tags", []):
                product.tags.append(ProductTag(tag=t))

            # Images
            for i, img_url in enumerate(item.get("images", [])):
                product.images.append(ProductImage(image_url=img_url, position=i))

            # Reviews
            for rev in item.get("reviews", []):
                product.reviews.append(Review(
                    rating=rev.get("rating", 0),
                    comment=rev.get("comment"),
                    reviewer_name=rev.get("reviewerName"),
                    reviewer_email=rev.get("reviewerEmail"),
                    review_date=parse_iso_datetime(rev.get("date"))
                ))

            db_products.append(product)

        db.add_all(db_products)
        db.commit()
        logger.info("Inserted %s products into MySQL", len(db_products))

        IngestionService.index_documents(products)

    @staticmethod
    def index_documents(products: list[dict]) -> None:
        actions = []
        for item in products:
            # We index exactly as provided by the DummyJSON schema, adapting property names if necessary,
            # or we can push it straightforwardly. Let's align it with out to_dict keys if needed.
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
                "weight": item.get("weight"),
                "warranty_information": item.get("warrantyInformation"),
                "shipping_information": item.get("shippingInformation"),
                "availability_status": item.get("availabilityStatus"),
                "return_policy": item.get("returnPolicy"),
                "minimum_order_quantity": item.get("minimumOrderQuantity"),
                "dimensions": item.get("dimensions", {}),
                "meta": item.get("meta", {}),
                "tags": item.get("tags", []),
                "images": item.get("images", []),
                "reviews": item.get("reviews", [])
            }
            actions.append({"index": {"_index": settings.ELASTICSEARCH_INDEX, "_id": item["id"]}})
            actions.append(doc)

        if actions:
            es_client.bulk(operations=actions, refresh=True)
            logger.info("Indexed %s products into Elasticsearch", len(products))

    @staticmethod
    def index_all_from_db(db: Session) -> None:
        products = db.scalars(select(Product)).all()
        # to_dict returns exactly the formatted document
        payload = [p.to_dict() for p in products]

        actions = []
        for item in payload:
            actions.append({"index": {"_index": settings.ELASTICSEARCH_INDEX, "_id": item["id"]}})
            actions.append(item)

        if actions:
            es_client.bulk(operations=actions, refresh=True)
            logger.info("Re-indexed %s products from MySQL into Elasticsearch", len(payload))