# FastAPI CRUD with PostgreSQL

A production-ready FastAPI application with PostgreSQL database, featuring async SQLAlchemy, Alembic migrations, Docker support, and comprehensive tests.

## Features

- ✅ Async FastAPI application
- ✅ PostgreSQL database with SQLAlchemy 2.0
- ✅ Database migrations with Alembic
- ✅ CRUD operations (Create, Read, Update, Delete)
- ✅ Request/response validation with Pydantic
- ✅ Pagination support
- ✅ Dependency injection
- ✅ Comprehensive tests with pytest
- ✅ Docker and Docker Compose support
- ✅ pgAdmin for database management

## Quick Start

### Option 1: Run with Docker Compose (Recommended)

```bash
# Start all services (app + PostgreSQL + pgAdmin)
docker-compose up -d

# View logs
docker-compose logs -f app

# Run database migrations
docker-compose exec app alembic upgrade head

# Stop services
docker-compose down
```

### Option 2: Run Locally

**Prerequisites:**
- Python 3.11+
- PostgreSQL 15+

**Steps:**

```bash
# 1. Install dependencies
pip install -r requirements.txt
# or with uv
uv sync

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your database credentials

# 3. Run database migrations
alembic upgrade head

# 4. Start the application
uvicorn app.main:app --reload
```

## Project Structure

```
crud-postgres/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database configuration
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── dependencies.py      # Dependency injection
│   └── routers/
│       ├── __init__.py
│       └── items.py         # Item endpoints
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Test fixtures
│   └── test_items.py        # Item tests
├── alembic/                 # Database migrations
├── requirements.txt         # Python dependencies
├── pyproject.toml           # Project configuration
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Multi-container setup
├── .env.example             # Environment template
└── README.md                # This file
```

## API Endpoints

### Root
- `GET /` - Welcome message
- `GET /health` - Health check

### Items
- `POST /items/` - Create a new item
- `GET /items/` - List items (with pagination)
- `GET /items/count` - Get total count of items
- `GET /items/{item_id}` - Get a specific item
- `PUT /items/{item_id}` - Update an item
- `DELETE /items/{item_id}` - Delete an item

## API Documentation

Once the application is running, access:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **pgAdmin:** http://localhost:5050 (user: admin@admin.com, password: admin)

## Example Usage

### Create an Item

```bash
curl -X POST "http://localhost:8000/items/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop",
    "description": "A powerful laptop for development",
    "price": 1299.99
  }'
```

### List Items with Pagination

```bash
curl "http://localhost:8000/items/?skip=0&limit=10"
```

### Get Specific Item

```bash
curl "http://localhost:8000/items/1"
```

### Update Item

```bash
curl -X PUT "http://localhost:8000/items/1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Laptop",
    "price": 1099.99
  }'
```

### Delete Item

```bash
curl -X DELETE "http://localhost:8000/items/1"
```

## Database Migrations

### Initialize Alembic (First Time Setup)

```bash
# Already configured - skip if alembic/ directory exists
alembic init alembic
```

### Create a New Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Or create empty migration
alembic revision -m "Description"
```

### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade one version
alembic upgrade +1

# Downgrade one version
alembic downgrade -1

# View migration history
alembic history

# View current version
alembic current
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_items.py

# Run specific test
pytest tests/test_items.py::test_create_item

# View coverage report
open htmlcov/index.html
```

## Development

### Local Development with Auto-Reload

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access PostgreSQL Database

**Using psql:**

```bash
psql -h localhost -U postgres -d fastapi_db
```

**Using pgAdmin:**

1. Open http://localhost:5050
2. Login: admin@admin.com / admin
3. Add server:
   - Host: db (or localhost if not using Docker)
   - Port: 5432
   - Database: fastapi_db
   - Username: postgres
   - Password: postgres

## Environment Variables

Create a `.env` file from `.env.example`:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/fastapi_db
DEBUG=True
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key-change-this-in-production
```

## Deployment

### Docker

```bash
# Build image
docker build -t fastapi-crud-app .

# Run container
docker run -d --name fastapi-app -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db \
  fastapi-crud-app
```

### Docker Compose (Production)

1. Update `docker-compose.yml` with production settings
2. Use strong passwords and secrets
3. Enable HTTPS with reverse proxy (Nginx/Caddy)
4. Set up backups for PostgreSQL data volume

## Production Checklist

- [ ] Change all default passwords
- [ ] Use strong SECRET_KEY (32+ random characters)
- [ ] Set DEBUG=False
- [ ] Use environment variables for all secrets
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS properly
- [ ] Set up database backups
- [ ] Configure logging and monitoring
- [ ] Use connection pooling
- [ ] Set resource limits (CPU/memory)
- [ ] Implement rate limiting
- [ ] Add authentication (see authentication.md reference)

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps

# View PostgreSQL logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Migration Issues

```bash
# Reset database (WARNING: deletes all data)
alembic downgrade base
alembic upgrade head

# Or drop and recreate
docker-compose down -v
docker-compose up -d
docker-compose exec app alembic upgrade head
```

### Permission Issues

```bash
# Fix file permissions
chmod -R 755 .
```

## Next Steps

1. **Add Authentication:** Implement JWT-based auth (see `references/authentication.md`)
2. **Add More Models:** Create users, categories, etc.
3. **Add Relationships:** Link items to users/categories
4. **Add Background Tasks:** Use Celery or FastAPI Background Tasks
5. **Add Caching:** Implement Redis caching
6. **Add Monitoring:** Set up logging, metrics, and alerts
7. **Deploy to Cloud:** AWS, GCP, Azure, or DigitalOcean

## Learn More

- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **SQLAlchemy Documentation:** https://docs.sqlalchemy.org/
- **Alembic Documentation:** https://alembic.sqlalchemy.org/
- **FastAPI Builder Skill References:**
  - `references/core-patterns.md` - FastAPI fundamentals
  - `references/database.md` - Advanced database patterns
  - `references/authentication.md` - Add user authentication
  - `references/testing.md` - Advanced testing patterns
  - `references/deployment.md` - Production deployment strategies

## License

This is a template project. Use it freely for your own projects.
