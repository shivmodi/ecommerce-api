import logging
from app.core.config import settings
from app.elasticsearch.client import es_client

logger = logging.getLogger(__name__)


def create_products_index() -> None:
    index_name = settings.ELASTICSEARCH_INDEX

    if es_client.indices.exists(index=index_name):
        logger.info("Elasticsearch index '%s' already exists", index_name)
        return

    mapping = {
        "settings": {
            "analysis": {
                "analyzer": {
                    "default": {
                        "type": "standard"
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "id": {"type": "integer"},
                "title": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "description": {"type": "text"},
                "category": {"type": "keyword"},
                "brand": {"type": "keyword"},
                "sku": {"type": "keyword"},
                "price": {"type": "float"},
                "discount_percentage": {"type": "float"},
                "rating": {"type": "float"},
                "stock": {"type": "integer"},
                "thumbnail": {"type": "keyword"},
                "weight": {"type": "float"},
                "warranty_information": {"type": "text"},
                "shipping_information": {"type": "text"},
                "availability_status": {"type": "keyword"},
                "return_policy": {"type": "text"},
                "minimum_order_quantity": {"type": "integer"},
                "dimensions": {
                    "properties": {
                        "width": {"type": "float"},
                        "height": {"type": "float"},
                        "depth": {"type": "float"}
                    }
                },
                "meta": {
                    "properties": {
                        "createdAt": {"type": "date"},
                        "updatedAt": {"type": "date"},
                        "barcode": {"type": "keyword"},
                        "qrCode": {"type": "keyword"}
                    }
                },
                "tags": {"type": "keyword"},
                "images": {"type": "keyword"},
                "reviews": {
                    "type": "nested",
                    "properties": {
                        "rating": {"type": "float"},
                        "comment": {"type": "text"},
                        "reviewerName": {"type": "keyword"},
                        "reviewerEmail": {"type": "keyword"},
                        "date": {"type": "date"}
                    }
                }
            }
        },
    }

    es_client.indices.create(index=index_name, body=mapping)
    logger.info("Created Elasticsearch index '%s' with nested mappings", index_name)