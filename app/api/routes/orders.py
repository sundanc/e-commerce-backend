from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import stripe

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.schemas.order import Order as OrderSchema, OrderCreate

# Configure Stripe - Only if API key is available
stripe_available = bool(settings.STRIPE_API_KEY)
if stripe_available:
    try:
        stripe.api_key = settings.STRIPE_API_KEY
    except Exception:
        stripe_available = False

router = APIRouter()

@router.get("/", response_model=List[OrderSchema])
def get_user_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user's orders
    """
    orders = db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).all()
    return orders

@router.get("/{order_id}", response_model=OrderSchema)
def get_order(
    *,
    db: Session = Depends(get_db),
    order_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get specific order by ID
    """
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

def process_order_after_payment(db: Session, order_id: int):
    """Background task to update product stock after successful payment"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order or order.status != OrderStatus.PAID:
        return
    
    # Update product stock
    for item in order.items:
        if item.product_id:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                product.stock -= item.quantity
                db.add(product)
    
    db.commit()

@router.post("/", response_model=OrderSchema)
def create_order(
    *,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks,
    order_in: OrderCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create new order from user's cart
    """
    # Get user's cart
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Calculate total amount
    total_amount = 0
    order_items = []
    
    # Check product availability and gather order items
    for cart_item in cart.items:
        product = db.query(Product).filter(
            Product.id == cart_item.product_id,
            Product.is_active == True
        ).first()
        
        if not product:
            raise HTTPException(
                status_code=400,
                detail=f"Product with ID {cart_item.product_id} is no longer available"
            )
        
        if product.stock < cart_item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for {product.name}. Available: {product.stock}"
            )
        
        item_total = cart_item.quantity * product.price
        total_amount += item_total
        
        order_items.append({
            "product_id": product.id,
            "product_name": product.name,
            "quantity": cart_item.quantity,
            "unit_price": product.price
        })
    
    # Create payment intent with Stripe if API key is configured and valid
    payment_id = None
    if stripe_available:
        try:
            # Create a payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=int(total_amount * 100),  # Stripe uses cents
                currency="usd",
                payment_method_types=["card"],
                metadata={"user_id": current_user.id}
            )
            payment_id = payment_intent.id
        except Exception as e:
            # Just log the error but continue (for local development)
            print(f"Stripe error: {str(e)}")
    
    # Create the order
    order = Order(
        user_id=current_user.id,
        total_amount=total_amount,
        shipping_address=order_in.shipping_address,
        status=OrderStatus.PENDING,
        payment_id=payment_id
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # Create order items
    for item_data in order_items:
        order_item = OrderItem(
            order_id=order.id,
            **item_data
        )
        db.add(order_item)
    
    # For development mode without Stripe, just mark the order as PAID
    if not stripe_available:
        order.status = OrderStatus.PAID
    
    db.commit()
    db.refresh(order)
    
    # Clear the user's cart after order is placed
    for cart_item in cart.items:
        db.delete(cart_item)
    db.commit()
    
    # Update product stock in background
    background_tasks.add_task(process_order_after_payment, db, order.id)
    
    return order
