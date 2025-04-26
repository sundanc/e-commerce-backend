from typing import Any, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, desc

from app.api.deps import get_current_active_admin, get_db, limit_query_factory
from app.core.database import get_db
from app.models.product import Product
from app.models.user import User
from app.schemas.product import Product as ProductSchema, ProductCreate, ProductUpdate
from app.core.cache import cache_response, invalidate_cache

router = APIRouter()

# Create a limiter for product queries
limit_product_query = limit_query_factory(max_limit=100, default_limit=20)

@router.get("/", response_model=List[ProductSchema])
@cache_response(prefix="products", expire_seconds=300)  # Cache for 5 minutes
async def get_products(
    db: Session = Depends(get_db),
    pagination: Tuple[int, int] = Depends(limit_product_query),
    category: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0),  # Ensure non-negative price
    max_price: Optional[float] = Query(None, ge=0),  # Ensure non-negative price
    search: Optional[str] = Query(None, max_length=100),  # Limit search length to prevent DoS
) -> Any:
    """
    Retrieve products with optional filtering
    """
    skip, limit = pagination  # Unpack the pagination values
    query = db.query(Product).filter(Product.is_active == True)
    
    if category:
        query = query.filter(Product.category == category)
    
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    if search:
        # Use more efficient ILIKE with index if available
        query = query.filter(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%")
            )
        )
    
    # Apply limits for security and performance
    products = query.offset(skip).limit(limit).all()
    return products

@router.get("/{product_id}", response_model=ProductSchema)
def get_product(
    *,
    db: Session = Depends(get_db),
    product_id: int,
) -> Any:
    """
    Get product by ID
    """
    product = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/", response_model=ProductSchema)
async def create_product(
    *,
    db: Session = Depends(get_db),
    product_in: ProductCreate,
    current_user: User = Depends(get_current_active_admin),
) -> Any:
    """
    Create new product (admin only)
    """
    existing_product = db.query(Product).filter(Product.sku == product_in.sku).first()
    if existing_product:
        raise HTTPException(
            status_code=400,
            detail="Product with this SKU already exists",
        )
    
    product = Product(**product_in.dict())
    db.add(product)
    db.commit()
    db.refresh(product)
    
    # Invalidate product cache
    await invalidate_cache("products:*")
    
    return product

@router.put("/{product_id}", response_model=ProductSchema)
async def update_product(
    *,
    db: Session = Depends(get_db),
    product_id: int,
    product_in: ProductUpdate,
    current_user: User = Depends(get_current_active_admin),
) -> Any:
    """
    Update a product (admin only)
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.add(product)
    db.commit()
    db.refresh(product)
    
    # Invalidate product cache
    await invalidate_cache("products:*")
    
    return product

@router.delete("/{product_id}", response_model=ProductSchema)
async def delete_product(
    *,
    db: Session = Depends(get_db),
    product_id: int,
    current_user: User = Depends(get_current_active_admin),
) -> Any:
    """
    Delete a product (admin only)
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Soft delete - just mark as inactive
    product.is_active = False
    db.add(product)
    db.commit()
    db.refresh(product)
    
    # Invalidate product cache
    await invalidate_cache("products:*")
    
    return product
