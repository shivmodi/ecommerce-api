from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.product import CategoryListResponse
from app.services.product_service import ProductService

router = APIRouter(prefix="", tags=["Categories"])


@router.get("/categories", response_model=CategoryListResponse)
def list_categories(db: Session = Depends(get_db)):
    categories = ProductService.get_categories(db)
    return {"categories": categories}