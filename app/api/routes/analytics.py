from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.api.deps import get_db, get_current_active_admin
from app.models.user import User
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product

router = APIRouter()

@router.get("/sales", response_model=Dict[str, Any])
async def get_sales_analytics(
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    period: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    current_user: User = Depends(get_current_active_admin),
) -> Any:
    """
    Get sales analytics (admin only)
    """
    # Default to last 30 days if no date range provided
    if not end_date:
        end_date = datetime.now()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Query for completed orders
    query = db.query(
        func.date_trunc(period, Order.created_at).label('period'),
        func.count(Order.id).label('order_count'),
        func.sum(Order.total_amount).label('revenue')
    ).filter(
        Order.created_at.between(start_date, end_date),
        Order.status == OrderStatus.PAID
    ).group_by(
        func.date_trunc(period, Order.created_at)
    ).order_by(
        func.date_trunc(period, Order.created_at)
    )
    
    sales_data = query.all()
    
    # Format results
    result = {
        "timeframe": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "period": period,
        },
        "data": [
            {
                "date": row.period.isoformat(),
                "order_count": row.order_count,
                "revenue": float(row.revenue) if row.revenue else 0
            }
            for row in sales_data
        ]
    }
    
    # Add summary statistics
    total_orders = sum(item["order_count"] for item in result["data"])
    total_revenue = sum(item["revenue"] for item in result["data"])
    
    result["summary"] = {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "average_order_value": total_revenue / total_orders if total_orders > 0 else 0
    }
    
    return result

@router.get("/top-products", response_model=List[Dict[str, Any]])
async def get_top_products(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=50),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_admin),
) -> Any:
    """
    Get top selling products (admin only)
    """
    start_date = datetime.now() - timedelta(days=days)
    
    # Query for top products
    query = db.query(
        OrderItem.product_name,
        func.sum(OrderItem.quantity).label('units_sold'),
        func.sum(OrderItem.quantity * OrderItem.unit_price).label('revenue'),
        Product.id,
        Product.stock
    ).join(
        Order, OrderItem.order_id == Order.id
    ).outerjoin(  # Outer join because the product might have been deleted
        Product, OrderItem.product_id == Product.id
    ).filter(
        Order.created_at >= start_date,
        Order.status == OrderStatus.PAID
    ).group_by(
        OrderItem.product_name,
        Product.id,
        Product.stock
    ).order_by(
        desc('revenue')
    ).limit(limit)
    
    products = query.all()
    
    # Format results
    result = [
        {
            "product_name": product.product_name,
            "product_id": product.id,
            "units_sold": product.units_sold,
            "revenue": float(product.revenue),
            "current_stock": product.stock if product.stock is not None else "Product Removed"
        }
        for product in products
    ]
    
    return result
