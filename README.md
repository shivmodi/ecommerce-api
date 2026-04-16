# ConverzAI E-Commerce API

## 1. Prerequisites & Version Checks
Before installing anything, let's verify if you already have the required tools installed.

### Step 1: Check Docker Installation
This project runs entirely inside Docker. Open your terminal (PowerShell, Command Prompt, or Git Bash) and run:
```bash
docker --version
```
- **If it says `Docker version 20.x.x` (or higher):** You are good to go!
- **If it says `command not found` or `isn't recognized`:** You need to install Docker Desktop.
  - **Download:** [Docker Desktop Official Site](https://www.docker.com/products/docker-desktop/)
  - **Note for Windows:** Ensure WSL2 (Windows Subsystem for Linux) is enabled during installation.

### Step 2: Check Docker Compose Installation
```bash
docker-compose --version
```
- **If it returns a version (e.g., `1.29.x` or `2.x.x`):** You are good! (Docker Desktop usually installs this automatically).
- **If not recognized:** Update your Docker Desktop to the latest version.

### *(Optional) Check Python Version* 
*Note: You do not need Python installed locally to run this project because it runs inside Docker. But if you want to run it without Docker:*
```bash
python --version
```
- **Requirement:** You need **Python 3.10 or higher**.

---

## 2. Project Setup & Execution (Strict Order)
Follow this exact sequence to avoid database connection or indexing failures.

### Step 1: Open your Terminal
Navigate to your project directory:
```bash
cd "C:\Users\Mrinal Pandey\Downloads\conv AI assign\ecommerce-api"
```

### Step 2: Start and Build the Docker Services
Run the following command. The `--build` flag forces Docker to install the Python packages from `requirements.txt` into the app container.
```bash
docker-compose up --build -d
```
*(The `-d` flag runs the containers in the background, keeping your terminal free).*

### Step 3: Wait for Services to be Ready
Your `docker-compose.yml` has health checks built in. It takes around 30 to 60 seconds for MySQL and Elasticsearch to fully boot up. To watch the application progress, view the logs:
```bash
docker logs -f ecommerce_app
```
*Wait until you see:*
- `"Creating database tables..."`
- `"Bootstrapping data..."`
- `"Application startup completed."`
*(Press `Ctrl+C` to exit the logs)*

---

## 3. Verification Checklist

- [ ] **Docker Containers:** Run `docker ps`. You should see 3 containers (`ecommerce_mysql`, `ecommerce_elasticsearch`, `ecommerce_app`) running.
- [ ] **Health API:** Open `http://localhost:8000/health` in your browser. It should display `{"status":"ok"}`.
- [ ] **Swagger Documentation:** Go to `http://localhost:8000/docs` to see the auto-generated FastAPI interface.

---

## 4. API Testing

You can use `curl` in your terminal or a tool like [Postman](https://www.postman.com/downloads/).

**1. List Categories**
```bash
curl http://localhost:8000/categories
```

**2. List All Products (Paginated)**
```bash
curl "http://localhost:8000/products?page=1&size=5"
```

**3. Get a Single Product**
```bash
curl http://localhost:8000/products/1
```

**4. Search Full Text (via Elasticsearch)**
```bash
curl "http://localhost:8000/products?query=phone"
```

---

## 5. Common Issues & Troubleshooting

### Issue 1: Elasticsearch exits with Code 137 (Out of Memory)
- **Cause:** Docker Desktop on Windows doesn't have enough RAM allocated, and Elasticsearch uses a lot of memory.
- **Fix:** Open Docker Desktop Settings > Resources > Advanced, and allocate at least **4GB to 6GB** of memory to Docker. Restart Docker and try again.

### Issue 2: `ecommerce_app` container keeps restarting / crashing
- **Cause:** The app might ping MySQL before MySQL has fully completed its internal startup.
- **Fix:** Simply manually restart the app container once the DB is up:
  ```bash
  docker restart ecommerce_app
  ```

### Issue 3: Port 3306 or 8000 is already in use
- **Cause:** Another MySQL server (like XAMPP) or web service is running locally on your PC.
- **Fix:** Change the exposed port in `docker-compose.yml`. For example, change the App ports to `"8080:8000"` or MySQL to `"3308:3306"`. 

---
### Clean Up
To stop everything and shut down the containers:
```bash
docker-compose down
```
*(Use `docker-compose down -v` to entirely delete your local container data/volumes).*
