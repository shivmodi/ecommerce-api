from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    category: str
    brand: Optional[str] = None
    sku: Optional[str] = None
    price: float
    discount_percentage: Optional[float] = None
    rating: Optional[float] = None
    stock: Optional[int] = None
    thumbnail: Optional[str] = None


class ProductListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[ProductResponse]


class CategoryListResponse(BaseModel):
    categories: List[str]