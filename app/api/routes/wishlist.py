from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.product import Product
from app.models.wishlist import WishlistItem
from app.schemas.product import Product as ProductSchema

router = APIRouter()

@router.get("/", response_model=List[ProductSchema])
async def get_wishlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user's wishlist
    """
    wishlist_items = (
        db.query(Product)
        .join(WishlistItem, WishlistItem.product_id == Product.id)
        .filter(WishlistItem.user_id == current_user.id, Product.is_active == True)
        .all()
    )
    
    return wishlist_items

@router.post("/{product_id}", response_model=dict)
async def add_to_wishlist(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Add a product to the wishlist
    """
    # Check if product exists and is active
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_active == True
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or inactive")
    
    # Add to wishlist
    wishlist_item = WishlistItem(user_id=current_user.id, product_id=product_id)
    
    try:
        db.add(wishlist_item)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Product already in wishlist")
    
    return {"message": "Product added to wishlist"}

@router.delete("/{product_id}", response_model=dict)
async def remove_from_wishlist(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Remove a product from the wishlist
    """
    wishlist_item = db.query(WishlistItem).filter(
        WishlistItem.user_id == current_user.id,
        WishlistItem.product_id == product_id
    ).first()
    
    if not wishlist_item:
        raise HTTPException(status_code=404, detail="Product not found in wishlist")
    
    db.delete(wishlist_item)
    db.commit()
    
    return {"message": "Product removed from wishlist"}
