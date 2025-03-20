from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, validator

from app.schemas.product import Product


# Cart Item schemas
class CartItemBase(BaseModel):
    product_id: int
    quantity: int
    
    @validator('quantity')
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v


class CartItemCreate(CartItemBase):
    pass


class CartItemUpdate(BaseModel):
    quantity: int
    
    @validator('quantity')
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v


class CartItemInDBBase(CartItemBase):
    id: int
    cart_id: int
    unit_price: float
    
    class Config:
        orm_mode = True


class CartItemInDB(CartItemInDBBase):
    pass


class CartItem(CartItemInDBBase):
    product: Product


# Cart schemas
class CartBase(BaseModel):
    user_id: int


class CartCreate(CartBase):
    pass


class CartInDBBase(CartBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class Cart(CartInDBBase):
    items: List[CartItem] = []
    total: float = 0
