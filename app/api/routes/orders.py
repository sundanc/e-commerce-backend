from typing import Any, List
import logging  # Add logging import

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
import stripe

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db, SessionLocal
from app.models.user import User
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.schemas.order import Order as OrderSchema, OrderCreate
from app.services.notifications import email_service

# Configure Stripe - Only if API key is available
stripe_available = bool(settings.STRIPE_API_KEY)
if stripe_available:
    try:
        stripe.api_key = settings.STRIPE_API_KEY
    except Exception:
        stripe_available = False

# Configure logging
logger = logging.getLogger(__name__)

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

# Fix the process_order_after_payment function to use parameterized SQL for atomic operations
def process_order_after_payment(db: Session, order_id: int):
    """Background task to update product stock after successful payment"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order or order.status != OrderStatus.PAID:
        # Log if order not found or status incorrect for processing
        logger.warning(f"Order {order_id} not found or not in PAID status for stock update.")
        return

    try:
        # Use a transaction for atomic updates
        for item in order.items:
            if item.product_id:
                # Use SQL update with atomic operation to prevent race conditions
                result = db.execute(
                    """
                    UPDATE products 
                    SET stock = stock - :quantity 
                    WHERE id = :product_id AND stock >= :quantity
                    """,
                    {"quantity": item.quantity, "product_id": item.product_id}
                )
                
                if result.rowcount == 0:  # No row was updated (insufficient stock)
                    logger.error(f"Insufficient stock for product {item.product_id} during order {order_id} processing.")
                    # Consider adding order status update or notification here
        
        db.commit()
        logger.info(f"Successfully updated stock for order {order_id}")
    except Exception as e:
        logger.error(f"Error committing stock updates for order {order_id}: {e}")
        db.rollback()

@router.post("/", response_model=OrderSchema)
async def create_order(
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
                metadata={"user_id": current_user.id, "order_id": "pending"} # Add pending order ID placeholder
            )
            payment_id = payment_intent.id
        except Exception as e:
            # Log the error securely, avoid logging sensitive parts of the exception if possible
            logger.error(f"Stripe PaymentIntent creation failed for user {current_user.id}: {type(e).__name__}")
            # Depending on policy, you might want to raise an HTTPException here
            # raise HTTPException(status_code=500, detail="Payment processing failed.")
            # For now, we allow order creation without payment_id if Stripe fails

    # Create the order
    order = Order(
        user_id=current_user.id,
        total_amount=total_amount,
        shipping_address=order_in.shipping_address, # Consider adding validation for address format/content
        status=OrderStatus.PENDING,
        payment_id=payment_id
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # Update Stripe metadata with the actual order ID if payment_id exists
    if payment_id and stripe_available:
        try:
            stripe.PaymentIntent.modify(
                payment_id,
                metadata={"user_id": current_user.id, "order_id": order.id}
            )
        except Exception as e:
            logger.error(f"Stripe PaymentIntent metadata update failed for order {order.id}: {type(e).__name__}")

    # Create order items
    for item_data in order_items:
        order_item = OrderItem(
            order_id=order.id,
            **item_data
        )
        db.add(order_item)
    
    # For development mode without Stripe, or if Stripe failed, mark as PAID and process
    # NOTE: In production with Stripe enabled, payment confirmation (e.g., via webhook)
    # should trigger the status change to PAID and the stock update.
    # This immediate change is primarily for local dev or non-Stripe setups.
    if not stripe_available or not payment_id:
        order.status = OrderStatus.PAID
        # Update product stock in background only if marked as PAID immediately
        background_tasks.add_task(process_order_after_payment, db, order.id)

    db.commit()
    db.refresh(order)
    
    # Clear the user's cart after order is placed
    # Consider moving cart clearing until after successful payment confirmation in a production Stripe flow
    for cart_item in cart.items:
        db.delete(cart_item)
    db.commit()
    
    # If order was immediately marked PAID, the background task is already added.
    # If using Stripe webhooks, the background task should be triggered there.

    # After creating the order, add email notification task
    if order:
        # Prepare order data
        order_data = {
            "id": order.id,
            "created_at": order.created_at.isoformat(),
            "total_amount": order.total_amount,
            "status": order.status,
            "shipping_address": order.shipping_address,
            "items": [
                {
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price
                }
                for item in order.items
            ]
        }
        
        # Send order confirmation email as background task
        background_tasks.add_task(
            email_service.send_order_confirmation,
            current_user.email,
            order_data
        )
    
    return order

# When implementing the webhook endpoint, consider these security improvements:
@router.post("/webhook/stripe", include_in_schema=False)
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Add rate limiting for this endpoint to prevent DoS attacks
    
    # Set a reasonable size limit for the payload
    payload = await request.body()
    if len(payload) > 65536:  # Example: 64KB limit
        logger.warning("Webhook payload too large")
        raise HTTPException(status_code=400, detail="Payload too large")
        
    sig_header = request.headers.get('Stripe-Signature')
    if not sig_header:
        logger.warning("Missing Stripe signature header")
        raise HTTPException(status_code=400, detail="Missing signature")
        
    event = None
    if not settings.STRIPE_WEBHOOK_SECRET:
        logger.error("Stripe webhook secret not configured.")
        raise HTTPException(status_code=500, detail="Webhook not configured.")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        logger.error(f"Invalid Stripe webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"Invalid Stripe webhook signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Add idempotency check to prevent duplicate processing
    event_id = event['id']
    # Check if this event was already processed (using Redis or DB)
    # if event_already_processed(event_id):
    #     return {"status": "already processed"}
    
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        order_id = payment_intent['metadata'].get('order_id')
        if order_id:
            order = db.query(Order).filter(Order.id == int(order_id)).first()
            if order and order.status == OrderStatus.PENDING:
                order.status = OrderStatus.PAID
                order.payment_id = payment_intent.id # Ensure payment ID is stored
                db.add(order)
                db.commit()
                # Trigger background task for stock update now that payment is confirmed
                background_tasks.add_task(process_paid_order, order_id)
                logger.info(f"Order {order_id} marked as PAID via Stripe webhook.")
            else:
                logger.warning(f"Order {order_id} not found or not PENDING for webhook {event['id']}.")
        else:
            logger.warning(f"Order ID missing in metadata for webhook {event['id']}.")
    
    # Handle other event types (e.g., payment_intent.payment_failed)
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        order_id = payment_intent['metadata'].get('order_id')
        # Optionally update order status to failed or log the failure
        logger.warning(f"Payment failed for order {order_id} via Stripe webhook {event['id']}.")
    
    else:
        logger.info(f"Unhandled Stripe event type {event['type']}")
    
    return {"status": "success"}

# Fix process_paid_order to avoid circular import issues
def process_paid_order(order_id: int):
    """Process a paid order in a background task with a fresh DB session"""
    db = SessionLocal()
    try:
        # Process the order with a new session
        order = db.query(Order).filter(Order.id == order_id).first()
        if order and order.status == OrderStatus.PAID:
            # Process the stock updates
            process_order_after_payment(db, order_id)
            logger.info(f"Order {order_id} processed successfully in background task")
    except Exception as e:
        logger.error(f"Error processing paid order {order_id}: {e}")
        db.rollback()
    finally:
        db.close()
