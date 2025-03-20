from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_admin
from app.core.database import get_db
from app.models.user import User
from app.models.order import Order, OrderStatus
from app.schemas.order import Order as OrderSchema, OrderUpdate

router = APIRouter()

@router.get("/orders", response_model=List[OrderSchema])
def get_all_orders(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status: OrderStatus = None,
    current_user: User = Depends(get_current_active_admin),
) -> Any:
    """
    Get all orders with optional status filter (admin only)
    """
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    return orders

@router.put("/orders/{order_id}", response_model=OrderSchema)
def update_order_status(
    *,
    db: Session = Depends(get_db),
    order_id: int,
    order_in: OrderUpdate,
    current_user: User = Depends(get_current_active_admin),
) -> Any:
    """
    Update order status (admin only)
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    update_data = order_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)
    
    db.add(order)
    db.commit()
    db.refresh(order)
    return order
