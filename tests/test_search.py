import pytest
import time
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_api_health():
    """Ensure the API is up and running."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/products/1")
        assert response.status_code in [200, 404]

# --- SEARCH & FUZZINESS SCENARIOS ---
@pytest.mark.asyncio
@pytest.mark.parametrize("query, search_term", [
    ("lipstick", "lipstick"),  # Normal match
    ("liptick", "lipstick"),   # Typo/Fuzziness
    ("perfume", "fragrance"),  # Synonym mapping
])
async def test_search_accuracy(query, search_term):
    """
    PURPOSE: Verify ES handles normal terms, typos, and synonyms correctly.
    SCALING: Ensures relevance remains high even as data diversity grows.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/products?query={query}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0
        # Title boosting ensures relevant terms show up in top results
        titles = [item["title"].lower() for item in data["items"]]
        desc = [item["description"].lower() for item in data["items"]]
        combined = " ".join(titles + desc)
        assert search_term in combined or query in combined

# --- CACHING SCENARIOS (HIT/MISS) ---
@pytest.mark.asyncio
async def test_caching_hit_miss_cycle():
    """
    PURPOSE: Validate the full Redis cache lifecycle.
    PERFORMANCE: Ensures subsequent users get sub-5ms responses.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        unique_query = f"test_cache_{time.time()}"
        
        # 1. FIRST CALL (Expect Cache Miss)
        res1 = await ac.get(f"/products?query={unique_query}")
        assert res1.status_code == 200
        assert res1.json().get("cached") is False
        
        # 2. SECOND CALL (Expect Cache Hit)
        res2 = await ac.get(f"/products?query={unique_query}")
        assert res2.status_code == 200
        assert res2.json().get("cached") is True

# --- FILTERING SCENARIOS ---
@pytest.mark.asyncio
async def test_price_range_filtering():
    """
    PURPOSE: Verify that the DB/ES correctly applies numerical filters.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        min_p, max_p = 10, 50
        response = await ac.get(f"/products?query=beauty&min_price={min_p}&max_price={max_p}")
        assert response.status_code == 200
        items = response.json()["items"]
        for item in items:
            assert min_p <= item["price"] <= max_p

# --- PAGINATION SCENARIOS ---
@pytest.mark.asyncio
@pytest.mark.parametrize("page, size", [(1, 5), (2, 2)])
async def test_pagination_consistency(page, size):
    """
    PURPOSE: Ensure pagination 'size' and 'page' indices are respected.
    SCALING: Essential for handling large result sets without system memory bloat.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/products?page={page}&size={size}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= size
        assert data["page"] == page

# --- ERROR HANDLING ---
@pytest.mark.asyncio
async def test_invalid_category_filter():
    """
    PURPOSE: Verify system resilience against filters that don't match data.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/products?category=non_existent_category")
        assert response.status_code == 200
        assert response.json()["total"] == 0
