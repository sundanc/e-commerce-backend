"""
Setup script to initialize database and add test data for local development.
Run this script after setting up your .env file:

python setup_local.py
"""
import os
import sys
from pathlib import Path

# Ensure the script can import from the app package
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User
from app.models.product import Product
from app.core.database import Base

# Security warning
print("WARNING: This script creates users with preset passwords for DEVELOPMENT USE ONLY.")
print("         Never use these credentials in a production environment!")
print("=" * 80)

# Check if running in a production environment
if os.getenv("ENVIRONMENT", "").lower() == "production":
    print("ERROR: This script should not be run in production environments!")
    sys.exit(1)

# Improve error handling for database operations
try:
    # Create engine for database (moved inside try block)
    if settings.DATABASE_URL.startswith("sqlite"):
        engine = create_engine(
            settings.DATABASE_URL, connect_args={"check_same_thread": False}
        )
    else:
        engine = create_engine(settings.DATABASE_URL)

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    # Check if any users already exist
    existing_user = db.query(User).first()

    if not existing_user:
        print("Creating test users...")
        # Create admin user
        admin_user = User(
            email="admin@example.com",
            username="admin",
            hashed_password=get_password_hash("admin123"),
            full_name="Admin User",
            is_active=True,
            is_admin=True,
        )
        db.add(admin_user)

        # Create regular user
        regular_user = User(
            email="user@example.com",
            username="user",
            hashed_password=get_password_hash("user123"),
            full_name="Regular User",
            is_active=True,
            is_admin=False,
        )
        db.add(regular_user)
        db.commit()
        print("Test users created.")

    # Check if any products already exist
    existing_product = db.query(Product).first()

    if not existing_product:
        print("Creating test products...")
        # Create some test products
        products = [
            Product(
                name="Laptop",
                description="Powerful laptop with high performance",
                price=999.99,
                image_url="https://example.com/laptop.jpg",
                stock=10,
                category="Electronics",
                sku="TECH-001",
            ),
            Product(
                name="Smartphone",
                description="Latest smartphone with amazing camera",
                price=499.99,
                image_url="https://example.com/smartphone.jpg",
                stock=20,
                category="Electronics",
                sku="TECH-002",
            ),
            Product(
                name="Headphones",
                description="Noise cancelling wireless headphones",
                price=149.99,
                image_url="https://example.com/headphones.jpg",
                stock=30,
                category="Audio",
                sku="AUDIO-001",
            ),
            Product(
                name="Coffee Maker",
                description="Automatic coffee maker for your kitchen",
                price=79.99,
                image_url="https://example.com/coffeemaker.jpg",
                stock=15,
                category="Home",
                sku="HOME-001",
            ),
        ]
        for product in products:
            db.add(product)
        db.commit()
        print("Test products created.")

    print("Local setup completed successfully!")
except Exception as e:
    print(f"ERROR: Setup failed: {e}")
    sys.exit(1)
