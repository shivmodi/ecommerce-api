from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class DimensionsSchema(BaseModel):
    width: Optional[float] = None
    height: Optional[float] = None
    depth: Optional[float] = None

class MetaSchema(BaseModel):
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    barcode: Optional[str] = None
    qrCode: Optional[str] = None

class ReviewSchema(BaseModel):
    rating: float
    comment: Optional[str] = None
    reviewerName: Optional[str] = None
    reviewerEmail: Optional[str] = None
    date: Optional[datetime] = None

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
    weight: Optional[float] = None
    warranty_information: Optional[str] = None
    shipping_information: Optional[str] = None
    availability_status: Optional[str] = None
    return_policy: Optional[str] = None
    minimum_order_quantity: Optional[int] = None
    
    dimensions: Optional[DimensionsSchema] = None
    meta: Optional[MetaSchema] = None
    tags: List[str] = []
    images: List[str] = []
    reviews: List[ReviewSchema] = []

class AggregationBucket(BaseModel):
    key: str
    doc_count: int

class AggregationsSchema(BaseModel):
    categories: List[AggregationBucket] = []
    brands: List[AggregationBucket] = []

class ProductListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[ProductResponse]
    aggregations: Optional[AggregationsSchema] = None

class CategoryListResponse(BaseModel):
    categories: List[str]