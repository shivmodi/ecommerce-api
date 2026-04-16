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
            }
        },
    }

    es_client.indices.create(index=index_name, body=mapping)
    logger.info("Created Elasticsearch index '%s'", index_name)