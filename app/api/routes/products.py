from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.product import ProductResponse, ProductListResponse
from app.services.product_service import ProductService

router = APIRouter(prefix="", tags=["Products"])


@router.get("/products", response_model=ProductListResponse)
def list_or_search_products(
    query: Optional[str] = Query(default=None, description="Full-text search query"),
    category: Optional[str] = Query(default=None, description="Category filter"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    sort_by: str = Query(default="id"),
    sort_order: str = Query(default="asc"),
    db: Session = Depends(get_db),
):
    if query:
        result = ProductService.search_products(
            query=query,
            page=page,
            size=size,
            category=category,
        )
        return result

    result = ProductService.get_products(
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