from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Import all models here to register them with metadata
from app.db.models import Product, ProductTag, ProductImage, Review
