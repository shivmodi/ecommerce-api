from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.product import ProductResponse, ProductListResponse
from app.services.product_service import ProductService

router = APIRouter(prefix="", tags=["Products"])


@router.get("/products", response_model=ProductListResponse)
async def list_or_search_products(
    query: Optional[str] = Query(default=None, description="Full-text search query (uses Elasticsearch)"),
    category: Optional[str] = Query(default=None, description="Filter by exact category"),
    min_price: Optional[float] = Query(default=None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(default=None, ge=0, description="Maximum price filter"),
    min_rating: Optional[float] = Query(default=None, ge=0, le=5, description="Minimum rating filter"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    sort_by: str = Query(default="id", description="Sort field (id, price, title, rating, stock)"),
    sort_order: str = Query(default="asc", description="Sort order (asc or desc)"),
    db: Session = Depends(get_db),
):
    """
    DISCOVERY ENDPOINT:
    This endpoint allows users to find products via text search or filtered browsing.

    CONCEPTS:
    1. BRANCHING LOGIC:
       - If 'query' is provided -> Uses Elasticsearch (with Redis Caching)
       - If 'query' is missing  -> Uses MySQL (Standard Listing)

    2. CACHING:
       - Repeated search queries are served from Redis in ~1-5ms.
    """
    if query:
        result = await ProductService.search_products(
            query=query,
            page=page,
            size=size,
            category=category,
            min_price=min_price,
            max_price=max_price,
            min_rating=min_rating,
        )
        return result

    # Standard listing via MySQL (with Redis Caching)
    result = await ProductService.get_products(
        db=db,
        page=page,
        size=size,
        category=category,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return result


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_single_product(product_id: int, db: Session = Depends(get_db)):
    product = ProductService.get_product_by_id(db, product_id)
    return product