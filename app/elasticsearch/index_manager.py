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
    INITIAL USE:
    Configures the Elasticsearch 'Products' index with advanced settings for scaling (Sharding)
    and improved search quality (Synonyms/Analyzers).

    CONCEPTS:
    1. SHARDING (Scalability):
       - number_of_shards: 3. The index is split into 3 parts.
       - Logic: hash(id) % 3 determines which shard a product goes to.
       - Why: Allows searching in parallel across multiple servers.

    2. REPLICATION (High Availability):
       - number_of_replicas: 2. Each of the 3 shards has 2 copies.
       - Total physical shards = 3 * (1 + 2) = 9.
       - Why: Protects against server failure and speeds up read queries.

    3. ANALYSIS PIPELINE (Synonyms):
       - Pipeline: Standard Tokenizer -> Lowercase Filter -> Synonym Filter.
       - Example: "T-Shirt" becomes ["t-shirt", "tshirt", "tee"].
       - Why: Ensures users find what they need even if they use different words.
    """
    index_name = settings.ELASTICSEARCH_INDEX

    if es_client.indices.exists(index=index_name):
        logger.info("Elasticsearch index '%s' already exists", index_name)
        return

    synonyms = _load_synonyms()

    mapping = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,

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