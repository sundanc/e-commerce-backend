from typing import Optional
from datetime import datetime
from pydantic import BaseModel, validator


# Shared properties
class ProductBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    stock: Optional[int] = None
    is_active: Optional[bool] = True
    category: Optional[str] = None
    sku: Optional[str] = None


# Properties to receive on product creation
class ProductCreate(ProductBase):
    name: str
    price: float
    stock: int
    sku: str
    
    @validator('price')
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return v
    
    @validator('stock')
    def stock_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError('Stock cannot be negative')
        return v


# Properties to receive on product update
class ProductUpdate(ProductBase):
    pass


# Properties shared by models returned from API
class ProductInDBBase(ProductBase):
    id: int
    name: str
    price: float
    stock: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True


# Properties to return via API
class Product(ProductInDBBase):
    pass
