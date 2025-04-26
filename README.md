# 🛒 E-Commerce Backend API

![E-commerce Platform](https://img.shields.io/badge/Platform-E--Commerce-blue)
![Version](https://img.shields.io/badge/version-0.2.0-brightgreen) <!-- Updated version -->
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/Python-3.11+-yellow)
![FastAPI](https://img.shields.io/badge/FastAPI-Modern%20%26%20Fast-009688)

A robust, scalable, and secure RESTful API for e-commerce applications. Built with FastAPI, SQLAlchemy 2.0, PostgreSQL, Redis, and Docker.

[![Buy Me a Coffee](https://img.buymeacoffee.com/button-api/?text=Buy%20me%20a%20coffee&emoji=&slug=sundanc&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff)](https://www.buymeacoffee.com/sundanc)

## ✨ Features

- **🔐 Secure Authentication**: JWT-based authentication with JTI for potential revocation, token type validation, and role-based authorization.
- **👥 User Management**: Account creation, profiles, and permission controls.
- **📦 Product Catalog**: Comprehensive product management with searching and filtering.
- **🛒 Shopping Cart**: Flexible cart functionality with real-time stock validation.
- **💳 Order Processing**: End-to-end order lifecycle management with background processing and atomic stock updates.
- **💰 Payment Integration**: Seamless Stripe payment processing with webhook security.
- **🚚 Shipping Management**: Order tracking and status updates.
- **👑 Admin Dashboard API**: Complete administrative controls with proper permission checks.
- **⚡ Performance Optimized**: Redis caching for API responses and query optimization.
- **🛡️ API Protection**: Rate limiting implemented using SlowAPI and Redis.
- **🐳 Containerized**: Secure multi-stage Docker build & Docker Compose setup with non-root user and healthchecks.
- **🔒 Security Focused**: Comprehensive security controls, updated dependencies, and automated vulnerability scanning scripts.

## 🏗️ Architecture

Our e-commerce backend follows a clean, layered architecture:

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
- **SQLAlchemy 2.0**: Powerful ORM for database operations with transaction safety
- **PostgreSQL**: Robust relational database for production
- **SQLite**: Lightweight database for development and testing
- **Pydantic v2**: Data validation and settings management 
- **JWT**: Secure, stateless authentication with replay protection
- **Stripe API**: Enterprise-grade payment processing with webhook security
- **Redis**: High-performance caching, session management, and rate limiting
- **Alembic**: Database migration tool
- **Docker & Docker Compose**: Containerization with security best practices
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

**Important:** Before building the Docker image, you **must** update the `sha256:<PASTE_DIGEST_HERE>` placeholders in the `Dockerfile` with the latest digest for the `python:3.11-slim` image. You can find this digest on [Docker Hub](https://hub.docker.com/_/python/tags?page=1&name=3.11-slim) or by running `docker pull python:3.11-slim` and then `docker inspect python:3.11-slim | grep Digest` locally.

1.  **Configure Environment:** Ensure your `.env` file is correctly configured for the Docker environment (e.g., `DATABASE_URL=postgresql://postgres:postgres@db:5432/ecommerce`, `REDIS_URL=redis://redis:6379/0`).

2.  **Build and Run:**
    ```bash
    docker-compose up -d --build
    ```
    The API will be available at `http://localhost:8000`.

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
│   │   ├── limiter.py        # Rate limiting
│   │   └── database.py       # Database connection
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic schemas
│   ├── services/             # Business logic
│   └── utils/                # Utility functions
├── alembic/                  # Database migrations
├── scripts/                  # Helper scripts
│   └── security_scan.py      # Security vulnerability scanner
├── tests/                    # Test suite
├── docker-compose.yml        # Docker Compose configuration
├── Dockerfile                # Docker configuration
├── requirements.txt          # Python dependencies
└── setup_local.py            # Local development setup
```

### Testing Credentials

Default credentials for local development are created by the `setup_local.py` script. Please refer to the script for details. **Do not use these credentials in production.**

## 🔒 Security

This project implements comprehensive security measures to protect your e-commerce platform:

### Authentication & Authorization
- **Enhanced JWT Authentication**: Secure tokens with JTI tracking, proper algorithm validation, and replay protection
- **Role-Based Access Control**: Strict permission enforcement for user/admin operations
- **Password Security**: Bcrypt hashing with high work factor (12+ rounds)

### API Protection
- **Rate Limiting**: Protects authentication endpoints and API routes from abuse and brute-force attacks
- **Input Validation**: Thorough request validation with Pydantic schema enforcement
- **Query Limiting**: Protection against resource exhaustion with pagination limits
- **Security Headers**: Comprehensive set including CSP, HSTS, X-Content-Type-Options, and more
- **HTTPS Enforcement**: Automatic HTTP to HTTPS redirection in production

### Infrastructure Security
- **Non-root Container**: Docker containers run as unprivileged user
- **Docker Secrets**: Support for secure credential management in production
- **Dependency Scanning**: Built-in tools to detect vulnerabilities
- **Container Health Checks**: Monitoring and self-healing capabilities

### Data Protection
- **SQL Injection Prevention**: Parameterized queries and ORM protection
- **XSS Protection**: Content-Security-Policy and proper output encoding
- **CSRF Protection**: API design that mitigates cross-site request forgery
- **Audit Logging**: Security event tracking with request IDs

### Security Tools
We provide built-in security tools to help identify and mitigate vulnerabilities:

```bash
# Run the basic security scanner
python scripts/security_scan.py

# Run with detailed output
python scripts/security_scan.py --verbose

# Export results to JSON
python scripts/security_scan.py --json results.json

# Run comprehensive security audit
python security_audit.py
```

For complete implementation details, configuration options, and production recommendations, see our [SECURITY.md](./SECURITY.md) documentation.

## ⚡ Performance

The API is designed for high performance and scalability:

- **Async Endpoints**: Non-blocking request handling
- **Connection Pooling**: Efficient database connections with proper transaction isolation
- **Redis Caching**: Optimized data retrieval
- **Pagination**: For large result sets with DoS protection
- **Background Tasks**: For CPU-intensive operations with proper session management

## 🌟 Production Readiness

For production deployment, consider these additional steps:

1. Set up a proper CI/CD pipeline with security scanning
2. Configure HTTPS with a valid certificate
3. Set up database backups and recovery procedures
4. Configure proper monitoring and logging with alerts
5. Restrict CORS to trusted domains
6. Set up a reverse proxy (Nginx/Traefik)
7. Use Docker secrets for sensitive information
8. Implement token revocation and refresh mechanisms
9. Configure a Web Application Firewall (WAF)

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the amazing Python framework
- [SQLAlchemy](https://www.sqlalchemy.org/) for the powerful ORM
- [Stripe](https://stripe.com/) for payment processing capabilities
- All open-source projects that made this possible

---

<p align="center">Made with ❤️ by <a href="https://github.com/sundanc">Sundance</a> for modern e-commerce solutions</p>
