# 🛒 Scalable E-Commerce Search Engine (Production Ready)

This project is a high-performance e-commerce backend built with **FastAPI**, **MySQL**, **Elasticsearch**, and **Redis**. It demonstrates advanced search patterns, horizontal scaling, and low-latency data retrieval.

---

## 🏗️ Architecture & Features

### 1. Fuzziness (Typo Tolerance)
- **What**: Integrated `fuzziness: AUTO` in Elasticsearch.
- **Why**: Enhances user experience by correcting typos. If a user searches for **"laptp"**, they still get **"laptop"** results.
- **Example**: `query=liptick` -> Returns `lipstick` products.

### 2. Intelligent Caching (Redis)
- **What**: Multi-layered caching for both **Elasticsearch Search** and **MySQL Listing**.
- **Why**: Reduces DB load and ensures sub-5ms response times.
- **Dynamic Keys**: Cache keys are generated using every parameter (`min_price`, `category`, etc.) to ensure users never get "stale" or "incorrectly filtered" data.

### 3. Sharding & Replication
- **What**: Distributed index across multiple shards with replication.
- **Why**:
    - **Sharding**: Parallelizes search across nodes for massive datasets.
    - **Replication**: Provides fault tolerance (if one node crashes, data is safe) and boosts read performance.
- **Current Setup**: 2 Shards / 1 Replica (Optimized local/production balance).

### 4. Advanced Search Logic
- **Synonyms**: Multi-word mapping (e.g., "perfume" -> "fragrances") managed via `config/synonyms.txt`.
- **Field Boosting**: Titles are weighted **3x** higher than descriptions for maximum relevance.

### 5. Dynamic Pagination
- **What**: Efficient result slicing at the database layer (SQL Offset/Fetch) and Elasticsearch layer (`from`/`size`).
- **Why**: Prevents system "Memory Bloat." Without pagination, returning 10,000 products at once would crash the API and freeze the user's browser.

### 6. Resilient Ingestion (Retry Mechanism)
- **What**: Automated **Exponential Backoff** retry logic (Fixed at 3 attempts) during data fetching.
- **Why**: Protects against flaky network connections or temporary downtime of external product vendors, ensuring the local database is always fully populated.

---

## 🚀 How to Run the Project

### 1. Prerequisites
- Docker & Docker Compose installed.

### 2. Deployment
```bash
docker-compose up --build -d
```

### 🔌 Service Endpoints & Ports
| Service | Port | Description |
| :--- | :--- | :--- |
| **FastAPI** | `8000` | API & Swagger Docs (`/docs`) |
| **MySQL** | `3307` | Relational Data Store |
| **Elasticsearch** | `9200` | Search Engine |
| **Redis** | `6379` | Cache Layer |

---

## 🧪 Testing & Verification

Comprehensive test cases are provided using **pytest** and **httpx**.

### To Run the Full Test Suite:
Ensure your containers are running, then execute:
```bash
docker exec -it ecommerce_app pytest tests/
```

---

## 📋 Project Summary

### **✅ Current Features Added:**
- **Full-Text Search**: Typo tolerance (Fuzziness) and synonym mapping.
- **Dynamic Pagination**: Scalable result handling to prevent system memory bloat.
- **Resilient Ingestion**: **Retry Mechanism** (3 attempts) for external API fetches.
- **Category Filtering**: Exact match filtering for narrow discovery.
- **Price/Rating Ranges**: Numerical range filtering for budget searches.
- **Scalable Infrastructure**: Configured for 2 shards and 1 replica.
- **High-Speed Caching**: Redis integration for all main discovery paths.

### **⚠️ Current Limitations:**
- **Hardcoded Synonyms**: Synonyms are managed via a static file (`config/synonyms.txt`). In a future version, an API could be used to manage these dynamically.
- **Fixed Pagination Defaults**: The system defaults to `page=1` and `size=10`. While adjustable via queries, these global defaults are static.
- **Extraction Limit**: Data ingestion is currently capped at **200 products** to maintain stability during demonstration.

### **🔮 Future Improvements:**
1. **Auto-Complete & Suggestions**: Switching to `search_as_you_type` for real-time user feedback.
2. **Master-Slave Architecture**: As write operations increase, we can move to a Master (Writes) and multiple Slave (Reads) MySQL architecture to offload the primary database.
3. **Advanced Load Balancing**: Deploying Nginx to distribute traffic across a cluster of FastAPI nodes.
4. **Dynamic Synchronizing**: Moving from "Batch Ingestion" to real-time "CDC (Change Data Capture)" to keep ES and MySQL in sync instantly.
