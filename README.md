# 🛒 E-Commerce Backend API

![E-commerce Platform](https://img.shields.io/badge/Platform-E--Commerce-blue)
![Version](https://img.shields.io/badge/version-0.1.0-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/Python-3.11+-yellow)
![FastAPI](https://img.shields.io/badge/FastAPI-Modern%20%26%20Fast-009688)

A robust, scalable, and secure RESTful API for e-commerce applications. Built with FastAPI, SQLAlchemy, PostgreSQL, and Docker.

[![Buy Me a Coffee](https://img.buymeacoffee.com/button-api/?text=Buy%20me%20a%20coffee&emoji=&slug=sundanc&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff)](https://www.buymeacoffee.com/sundanc)

## ✨ Features

- **🔐 Secure Authentication**: JWT-based authentication and authorization system
- **👥 User Management**: Account creation, profiles, and role-based permissions
- **📦 Product Catalog**: Comprehensive product management with searching and filtering
- **🛒 Shopping Cart**: Flexible cart functionality with real-time stock validation
- **💳 Order Processing**: End-to-end order lifecycle management
- **💰 Payment Integration**: Seamless Stripe payment processing
- **🚚 Shipping Management**: Order tracking and status updates
- **👑 Admin Dashboard API**: Complete administrative controls
- **⚡ Performance Optimized**: Redis caching for high-performance operation
- **🐳 Containerized**: Docker & Docker Compose for easy deployment

## 🏗️ Architecture

My e-commerce backend follows a clean, layered architecture:

```
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│    API Layer      │     │   Service Layer   │     │    Data Layer     │
│   (Controllers)   │────>│  (Business Logic) │────>│   (Models/ORM)    │
└───────────────────┘     └───────────────────┘     └───────────────────┘
         │                                                    │
         │                                                    │
         ▼                                                    ▼
┌───────────────────┐                              ┌───────────────────┐
│     Security      │                              │     Database      │
│   (JWT, OAuth)    │                              │   (PostgreSQL)    │
└───────────────────┘                              └───────────────────┘
```

## 🔧 Technology Stack

- **FastAPI**: High-performance API framework with automatic OpenAPI documentation
- **SQLAlchemy**: Powerful ORM for database operations
- **PostgreSQL**: Robust relational database for production
- **SQLite**: Lightweight database for development and testing
- **Pydantic**: Data validation and settings management 
- **JWT**: Secure, stateless authentication
- **Stripe API**: Enterprise-grade payment processing
- **Redis**: High-performance caching and session management
- **Alembic**: Database migration tool
- **Docker & Docker Compose**: Containerization and orchestration
- **WebSockets**: Real-time order and notification updates

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose (for containerized deployment)
- Git

### Quick Start (Local Development)

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/e-commerce-backend.git
   cd e-commerce-backend
   ```

2. **Set up a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize the database with test data**
   ```bash
   python setup_local.py
   ```

6. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Access the API documentation**
   
   Open your browser and navigate to [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Docker Deployment

```bash
docker-compose up -d
```

## 📚 API Documentation

Once running, explore the interactive API documentation at `/docs` endpoint. My API follows RESTful principles with these main resources:

| Resource | Description |
|----------|-------------|
| `/api/auth` | Authentication endpoints (login, register) |
| `/api/users` | User profile management |
| `/api/products` | Product catalog with searching and filtering |
| `/api/cart` | Shopping cart management |
| `/api/orders` | Order processing and history |
| `/api/admin` | Administrative operations (protected) |

## 👨‍💻 Development

### Code Structure

```
e-commerce-backend/
├── app/                      # Application package
│   ├── api/                  # API endpoints
│   │   ├── deps.py           # Dependency injection
│   │   └── routes/           # API route modules
│   ├── core/                 # Core functionality
│   │   ├── config.py         # Configuration
│   │   ├── security.py       # Security utilities
│   │   └── database.py       # Database connection
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic schemas
│   ├── services/             # Business logic
│   └── utils/                # Utility functions
├── alembic/                  # Database migrations
├── tests/                    # Test suite
├── docker-compose.yml        # Docker Compose configuration
├── Dockerfile                # Docker configuration
├── requirements.txt          # Python dependencies
└── setup_local.py            # Local development setup
```

### Testing Credentials

For local development and testing, use these credentials:

- **Admin User**:
  - Email: admin@example.com
  - Password: admin123

- **Regular User**:
  - Email: user@example.com
  - Password: user123

## 🔒 Security

This project implements comprehensive security measures:

- **Authentication**: JWT tokens with configurable expiration
- **Password Storage**: Secure password hashing with bcrypt
- **Role-based Access Control**: Fine-grained permission control
- **Input Validation**: Thorough schema validation with Pydantic
- **SQL Injection Protection**: Parameterized queries via SQLAlchemy
- **API Security**: Proper CORS configuration and endpoint protection

For complete security details, see my [SECURITY.md](./SECURITY.md) documentation.

## ⚡ Performance

The API is designed for high performance and scalability:

- **Async Endpoints**: Non-blocking request handling
- **Connection Pooling**: Efficient database connections
- **Redis Caching**: Optimized data retrieval
- **Pagination**: For large result sets
- **Background Tasks**: For CPU-intensive operations

## 🌟 Production Readiness

For production deployment, consider these additional steps:

1. Set up a proper CI/CD pipeline
2. Configure HTTPS with a valid certificate
3. Set up database backups
4. Implement rate limiting
5. Configure proper monitoring and logging
6. Restrict CORS to trusted domains
7. Set up a reverse proxy (Nginx/Traefik)

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the amazing Python framework
- [SQLAlchemy](https://www.sqlalchemy.org/) for the powerful ORM
- [Stripe](https://stripe.com/) for payment processing capabilities
- All open-source projects that made this possible

---

<p align="center">Made with ❤️ by <a href="https://github.com/sundanc">Sundance</a> for modern e-commerce solutions</p>
