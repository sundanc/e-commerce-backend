from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    image_url = Column(String)
    stock = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True)
    category = Column(String, index=True)
    sku = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
