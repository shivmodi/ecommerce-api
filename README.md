This project is a high-performance e-commerce backend built with **FastAPI**, **MySQL**, **Elasticsearch**, and **Redis**. It demonstrates advanced search patterns, horizontal scaling, and low-latency data retrieval.

---

## 🧠 Technical Thought Process & Rationale

When designing this system, I prioritized **Search Quality** and **Performance (UX)** above all else:

1.  **Elasticsearch vs. MySQL SQL**: I chose Elasticsearch because traditional SQL `LIKE` queries are slow and lack "relevance scoring." ES allows us to perform **Fuzzy matching** and **Field Boosting** (Weighting titles higher than descriptions) for a superior user experience.
2.  **Multilayer Redis Caching**: For an e-commerce platform, 90% of searches are often for the same popular terms. By integrating Redis, we offload massive search requests from Elasticsearch and serve the results in **~2-5ms**, significantly reducing server costs and infra load.
3.  **Horizontal Scalability**: I configured the index with **2 Shards and 1 Replica**. This ensures that as your catalog grows from 200 products to 2 million, the system can scale effortlessly across multiple bare-metal or cloud instances.
4.  **Resilience (Retries)**: The data ingestion uses a **Retry mechanism** because outside APIs are often flaky; by implementing 3 attempts, we guarantee that our source-of-truth remains consistent.

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
## 🛠️ **Troubleshooting Docker Permissions Issue**

If you encounter a **"Permission Denied"** error while trying to run Docker commands, follow these steps to resolve the issue.

### **Issue**: "Permission Denied" error when running `docker ps` or `docker-compose up`.

---

### Step 1: **Add Your User to the Docker Group**

Run the following command to add your user to the Docker group:

```bash
sudo usermod -aG docker $USER
````

* After running this command, **log out** and **log back in** to apply the group membership changes.
* Alternatively, you can run:

```bash
newgrp docker
```

This will avoid logging out and apply the group changes in your current session.

---

### Step 2: **Verify Docker Access**

After logging back in (or using `newgrp docker`), verify that Docker is accessible by running:

```bash
docker ps
```

This should list the running Docker containers without any permission errors.

---

### Step 3: **Restart Docker Service**

If the issue persists, restart the Docker service with:

```bash
sudo systemctl restart docker
```

This will ensure that Docker picks up the changes to user permissions and settings.

---

### Step 4: **Check Docker Socket Permissions**

Ensure that the Docker socket has the correct permissions. Run:

```bash
sudo chown root:docker /var/run/docker.sock
sudo chmod 660 /var/run/docker.sock
```

This sets the appropriate read/write permissions for the Docker socket, allowing your user to interact with Docker.

---

### Step 5: **Re-run Docker Compose**

Once the above steps are completed, try running the following to start your containers:

```bash
docker-compose up --build -d
```

---

### ✅ **Accessing the Application**

Once your Docker containers are running, you can access the application via:

* **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

These links will take you to the interactive API documentation, where you can test the available endpoints.

---

### Conclusion

By following these steps, you should be able to resolve the Docker permission issues and run the application locally without any problems. Let me know if you encounter any other issues!

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
