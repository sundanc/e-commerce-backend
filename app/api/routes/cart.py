from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.schemas.cart import Cart as CartSchema, CartItemCreate, CartItemUpdate

router = APIRouter()

@router.get("/", response_model=CartSchema)
def get_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user's cart
    """
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    
    # Create cart if it doesn't exist
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    
    # Calculate total
    total = 0
    for item in cart.items:
        total += item.quantity * item.unit_price
    
    # Add total to cart object (it's not in the model)
    setattr(cart, "total", total)
    
    return cart

@router.post("/items", response_model=CartSchema)
def add_cart_item(
    *,
    db: Session = Depends(get_db),
    item_in: CartItemCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Add item to cart
    """
    # Get or create cart
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    
    # Check if product exists and is active
    product = db.query(Product).filter(
        Product.id == item_in.product_id,
        Product.is_active == True
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or inactive")
    
    # Check stock
    if product.stock < item_in.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock available")
    
    # Check if item already in cart
    cart_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == item_in.product_id
    ).first()
    
    if cart_item:
        # Update quantity if item exists
        if cart_item.quantity + item_in.quantity > product.stock:
            raise HTTPException(status_code=400, detail="Not enough stock available")
        
        cart_item.quantity += item_in.quantity
        cart_item.unit_price = product.price  # Update price in case it changed
    else:
        # Create new cart item
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=item_in.product_id,
            quantity=item_in.quantity,
            unit_price=product.price
        )
        db.add(cart_item)
    
    db.commit()
    db.refresh(cart)
    
    # Calculate total
    total = 0
    for item in cart.items:
        total += item.quantity * item.unit_price
    
    # Add total to cart object
    setattr(cart, "total", total)
    
    return cart

@router.put("/items/{item_id}", response_model=CartSchema)
def update_cart_item(
    *,
    db: Session = Depends(get_db),
    item_id: int,
    item_in: CartItemUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update cart item quantity
    """
    # Get cart
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    # Get cart item
    cart_item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.cart_id == cart.id
    ).first()
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    # Check stock
    product = db.query(Product).filter(Product.id == cart_item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if item_in.quantity > product.stock:
        raise HTTPException(status_code=400, detail="Not enough stock available")
    
    # Update quantity
    cart_item.quantity = item_in.quantity
    db.commit()
    db.refresh(cart)
    
    # Calculate total
    total = 0
    for item in cart.items:
        total += item.quantity * item.unit_price
    
    # Add total to cart object
    setattr(cart, "total", total)
    
    return cart

@router.delete("/items/{item_id}", response_model=CartSchema)
def remove_cart_item(
    *,
    db: Session = Depends(get_db),
    item_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Remove item from cart
    """
    # Get cart
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    # Get cart item
    cart_item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.cart_id == cart.id
    ).first()
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    # Remove item
    db.delete(cart_item)
    db.commit()
    db.refresh(cart)
    
    # Calculate total
    total = 0
    for item in cart.items:
        total += item.quantity * item.unit_price
    
    # Add total to cart object
    setattr(cart, "total", total)
    
    return cart
