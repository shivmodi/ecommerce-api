from decimal import Decimal
from sqlalchemy import Integer, String, Text, Numeric, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Product(Base):
    __tablename__ = "products"

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

    def to_dict(self) -> dict:
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
        }