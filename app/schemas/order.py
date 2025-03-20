from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.models.order import OrderStatus


# Order Item schemas
class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    unit_price: float


class OrderItemCreate(OrderItemBase):
    product_name: str


class OrderItemInDBBase(OrderItemBase):
    id: int
    order_id: int
    product_name: str
    
    class Config:
        orm_mode = True


class OrderItem(OrderItemInDBBase):
    pass


# Order schemas
class OrderBase(BaseModel):
    shipping_address: str


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    shipping_address: Optional[str] = None


class OrderInDBBase(OrderBase):
    id: int
    user_id: Optional[int] = None
    status: OrderStatus
    total_amount: float
    payment_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class Order(OrderInDBBase):
    items: List[OrderItem] = []
