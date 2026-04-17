from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.product import CategoryListResponse
from app.services.product_service import ProductService

router = APIRouter(prefix="", tags=["Categories"])


@router.get("/categories", response_model=CategoryListResponse)
def list_categories(db: Session = Depends(get_db)):
    """
    ### 📁 CATEGORY DISCOVERY
    Returns a unique list of all product categories available in the database.

    **WHY**: Essential for building dynamic navigational menus and front-end filters.
    
    **WHEN USEFUL**: 
    - Initial page load to populate sidebar filters.
    - SEO sitemaps generation.
    """
    categories = ProductService.get_categories(db)
    return {"categories": categories}