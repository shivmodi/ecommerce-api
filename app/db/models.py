from decimal import Decimal
from datetime import datetime
from sqlalchemy import Integer, String, Text, Numeric, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from app.db.base import Base

class ProductTag(Base):
    __tablename__ = "product_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    tag: Mapped[str] = mapped_column(String(100), nullable=False)

    product: Mapped["Product"] = relationship(back_populates="tags")

class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    image_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)

    product: Mapped["Product"] = relationship(back_populates="images")

class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    review_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    product: Mapped["Product"] = relationship(back_populates="reviews")

class Product(Base):
    """
    CONCEPT: RELATIONAL DATA MODEL (MySQL)
    This is the primary table for storing product information.

    RELATIONSHIPS:
    - tags: One-to-Many dependency (Product -> ProductTag)
    - images: One-to-Many dependency (Product -> ProductImage)
    - reviews: One-to-Many dependency (Product -> Review)

    DENORMALIZATION:
    - Dimensions and Meta are stored as flat columns (e.g., dimension_width) 
      for simplicity in MySQL, then nested in the to_dict() method for the API.
    """
    __tablename__ = "products"

    # Core Fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discount_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    stock: Mapped[int | None] = mapped_column(Integer, nullable=True)
    thumbnail: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Additional fields
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    warranty_information: Mapped[str | None] = mapped_column(String(255), nullable=True)
    shipping_information: Mapped[str | None] = mapped_column(String(255), nullable=True)
    availability_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    return_policy: Mapped[str | None] = mapped_column(String(255), nullable=True)
    minimum_order_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Dimensions
    dimension_width: Mapped[float | None] = mapped_column(Float, nullable=True)
    dimension_height: Mapped[float | None] = mapped_column(Float, nullable=True)
    dimension_depth: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Metadata
    meta_created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    meta_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    meta_barcode: Mapped[str | None] = mapped_column(String(100), nullable=True)
    meta_qr_code: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    tags: Mapped[List["ProductTag"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    images: Mapped[List["ProductImage"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    reviews: Mapped[List["Review"]] = relationship(back_populates="product", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        """
        NORMALIZATION:
        Converts the flat SQLAlchemy model into a nested Dictionary format 
        that matches the API expectations (and Elasticsearch format).
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "brand": self.brand,
            "sku": self.sku,
            "price": float(self.price),
            "discount_percentage": self.discount_percentage,
            "rating": self.rating,
            "stock": self.stock,
            "thumbnail": self.thumbnail,
            "weight": self.weight,
            "warranty_information": self.warranty_information,
            "shipping_information": self.shipping_information,
            "availability_status": self.availability_status,
            "return_policy": self.return_policy,
            "minimum_order_quantity": self.minimum_order_quantity,
            "dimensions": {
                "width": self.dimension_width,
                "height": self.dimension_height,
                "depth": self.dimension_depth,
                "position": "images" # Placeholder to explain thumbnail vs images logic
            },
            "meta": {
                "createdAt": self.meta_created_at.isoformat() if self.meta_created_at else None,
                "updatedAt": self.meta_updated_at.isoformat() if self.meta_updated_at else None,
                "barcode": self.meta_barcode,
                "qrCode": self.meta_qr_code,
            },
            "tags": [t.tag for t in self.tags],
            "images": [img.image_url for img in self.images],
            "reviews": [
                {
                    "rating": r.rating,
                    "comment": r.comment,
                    "reviewerName": r.reviewer_name,
                    "reviewerEmail": r.reviewer_email,
                    "date": r.review_date.isoformat() if r.review_date else None,
                }
                for r in self.reviews
            ]
        }