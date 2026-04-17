# 🏗️ System Design & Architecture

This document provides a technical deep-dive into the design decisions made for the E-Commerce Search API.

---

## 1. Data Flow Architecture
The system follows a "Write-Once, Search-Everywhere" pattern:
1. **Ingestion**: Data is fetched from an external API (DummyJSON) in batches of 200. We utilize a **Batch-Retry Mechanism** (3 attempts) to ensure data integrity during flaky network conditions.
2. **Pagination**: Managed at both the SQL and Elasticsearch layers to ensure the system handles thousands of records without memory spikes.
3. **Relational Storage (MySQL)**: Data is normalized into 4 tables (`products`, `product_tags`, `product_images`, `reviews`).
4. **Search Indexing (Elasticsearch)**: The normalized data is denormalized and indexed into Elasticsearch with custom analyzers.
5. **Caching (Redis)**: Search results are cached based on the full query context.

---

## 2. Advanced Search Features
### Fuzziness (Typo Tolerance)
- **Mechanism**: Level-Distance algorithm (Levenshtein).
- **Utility**: If a user is on a mobile device and makes a typo, the system automatically corrects it (e.g., "aple" -> "apple").
- **Benefit**: Reduces "Zero Results" pages significantly.

### Synonym Pipeline
- **Mechanism**: Custom analyzer using a `synonym_analyzer` filter.
- **Log Logic**: Synonyms are handled at **Query Time**. This means updating synonyms doesn't require re-indexing millions of products.
- **Hardcoded Rules**: Mappings such as "beauty" -> "cosmetics" are managed in `config/synonyms.txt`.

---

## 3. Scaling Strategy
### Horizontal Sharding
We use **2 Shards** per index. This allows Elasticsearch to split the workload across two CPU/Memory nodes, increasing the number of concurrent searches the system can handle.

### Replication for Fault Tolerance
We use **1 Replica** (total 2 copies of data). If one server in the cluster fails, the other immediately takes over without downtime.

---

## 4. Performance Optimization (Redis)
### Dynamic Cache Keys
We don't just cache the "word"; we cache the **entire context**. 
- **Key Format**: `search:p{page}:s{size}:q:{query}:c:{category}:minp:{min_price}`
- **Why**: This ensures that if User A filters by "Price < 100" and User B filters by "Price < 50", they don't accidentally see each other's cached data.

---

## 5. ⚠️ System Limitations
While the current architecture is robust, there are several production constraints:
- **Hardcoded Synonym Dictionary**: Synonym mappings are stored in a static text file (`config/synonyms.txt`). In a dynamic enterprise environment, we would migrate this to an Elasticsearch Synonym API or a management dashboard.
- **Extraction Cap**: The current ingestion service is capped at **200 products** to prevent throttling from the source API and ensure stable local bootstrapping.
- **Static Pagination Defaults**: Default values for `page` (1) and `size` (10) are defined at the application level. While overridable via query params, they are not dynamically adjusted based on client bandwidth or screen size.
- **In-Memory Cache (Local)**: Currently, Redis is used as a single instance. For high-availability, this should transition to **Redis Sentinel** or **Redis Cluster**.

---

## 🏁 Summary & Future Scaling
We have successfully implemented a core search engine with **Fuzziness**, **Pagination**, **Synonyms**, and **Caching**. 

To scale further as users grow:
1. **Search Suggest**: Implement "Did you mean?" logic for refined user discovery.
2. **Horizontal DB Scaling**: Implement **Master-Slave Replication for MySQL**. This allows us to perform expensive read operations (Analytics/Category Listings) on Slave nodes while keeping the Master dedicated to fast Write/Update operations.
3. **Global Load Balancing**: Introduce a load balancing layer to handle massive concurrent traffic spikes effortlessly.
