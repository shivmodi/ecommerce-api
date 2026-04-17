import logging
from app.core.config import settings
from app.elasticsearch.client import es_client

logger = logging.getLogger(__name__)

# Load synonyms from the external file at module load time
# Anyone can edit config/synonyms.txt to add synonyms — no Python changes needed!
def _load_synonyms() -> list[str]:
    import os
    synonyms = []
    # Path inside the container (mounted via docker-compose volume)
    synonyms_path = "/app/config/synonyms.txt"
    if not os.path.exists(synonyms_path):
        logger.warning("synonyms.txt not found at %s, using empty synonym list", synonyms_path)
        return synonyms
    with open(synonyms_path, "r") as f:
        for line in f:
            line = line.strip()
            # Skip blank lines and comment lines starting with #
            if line and not line.startswith("#"):
                synonyms.append(line)
    logger.info("Loaded %d synonym rules from %s", len(synonyms), synonyms_path)
    return synonyms
def create_products_index() -> None:
    """
    ### 🧱 ELASTICSEARCH INDEX ORCHESTRATION
    Configures the 'Products' index with advanced scaling and search logic.

    **WHY**: Default indices are not optimized for e-commerce. We need specific 
             settings for **Typo Tolerance**, **Synonyms**, and **Performance**.
    
    **WHEN USEFUL**: 
    - First-time setup (Index Initialization).
    - Deploying to a multi-node cluster (Horizontal Scaling).

    **FEATURES**:
    1. **SHARDING**: Splits data across 2 nodes (2 Shards) for parallel searching.
    2. **REPLICATION**: Creates 1 copy (1 Replica) of data for fault tolerance.
    3. **ANALYZERS**: Custom pipeline mapping "perfume" -> "fragrance" at ingestion.
    """
    index_name = settings.ELASTICSEARCH_INDEX

    if es_client.indices.exists(index=index_name):
        logger.info("SYSTEM | Index '%s' exists. Ready.", index_name)
        return

    synonyms = _load_synonyms()

    mapping = {
        "settings": {
            "number_of_shards": 2,
            "number_of_replicas": 1,

            "analysis": {
                "filter": {
                    "synonym_filter": {
                        "type": "synonym",
                        "synonyms": synonyms,
                    }
                },
                "analyzer": {
                    "synonym_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "synonym_filter"]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "id": {"type": "integer"},
                "title": {
                    "type": "text",
                    "analyzer": "synonym_analyzer",
                    "fields": {"keyword": {"type": "keyword"}}
                },
                "description": {
                    "type": "text",
                    "analyzer": "synonym_analyzer"
                },
                "category": {"type": "keyword"},
                "brand": {"type": "keyword"},
                "sku": {"type": "keyword"},
                "availability_status": {"type": "keyword"},
                "tags": {"type": "keyword"},
                "images": {"type": "keyword"},
                "price": {"type": "float"},
                "discount_percentage": {"type": "float"},
                "rating": {"type": "float"},
                "stock": {"type": "integer"},
                "weight": {"type": "float"},
                "minimum_order_quantity": {"type": "integer"},
                "thumbnail": {"type": "keyword"},
                "warranty_information": {"type": "text"},
                "shipping_information": {"type": "text"},
                "return_policy": {"type": "text"},
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
    logger.info(
        "Created Elasticsearch index '%s' with %d synonym rules and %d shards",
        index_name, len(synonyms), mapping["settings"]["number_of_shards"]
    )