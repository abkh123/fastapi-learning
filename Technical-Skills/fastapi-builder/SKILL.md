---
name: fastapi-builder
description: Build FastAPI projects from hello-world to production-ready APIs. Use when building REST APIs with Python, creating CRUD endpoints, adding authentication, integrating databases (PostgreSQL/SQLite/MongoDB), or deploying with Docker/Kubernetes. Supports project scaffolding, API patterns, testing, and deployment workflows.
---

# FastAPI Builder

Build FastAPI applications from simple prototypes to production-ready APIs with database integration, authentication, and deployment support.

## Quick Start

Choose your starting point based on your needs:

**New to FastAPI or building a simple API?**
→ Use the `hello-world` template

**Building a real application with a database?**
→ Use the `crud-postgres` template

**Adding specific features to an existing project?**
→ Consult the reference files below

## Project Templates

### Hello World Template

**When to use:**
- Learning FastAPI
- Prototyping APIs quickly
- Building simple APIs without a database
- Testing FastAPI features

**What's included:**
- Basic CRUD endpoints with in-memory storage
- Pydantic validation
- Docker support
- Interactive API documentation
- Health check endpoint

**Get started:**
```bash
# Copy the template
cp -r assets/hello-world/* ./my-project/
cd my-project

# Run locally
uv run uvicorn main:app --reload

# Or with Docker
docker build -t my-api .
docker run -p 8000:8000 my-api
```

**Files:** `main.py`, `requirements.txt`, `pyproject.toml`, `Dockerfile`, `README.md`

---

### CRUD + PostgreSQL Template

**When to use:**
- Building production applications
- Need persistent data storage
- Require database relationships
- Building scalable APIs

**What's included:**
- Async SQLAlchemy 2.0 with PostgreSQL
- Database migrations (Alembic)
- Structured project layout (app/ directory)
- Comprehensive tests with pytest
- Docker Compose (app + database + pgAdmin)
- Pagination and filtering patterns
- Production-ready Dockerfile

**Get started:**
```bash
# Copy the template
cp -r assets/crud-postgres/* ./my-project/
cd my-project

# Run with Docker Compose (easiest)
docker-compose up -d
docker-compose exec app alembic upgrade head

# Or run locally
cp .env.example .env
# Edit .env with your database credentials
uv sync
alembic upgrade head
uv run uvicorn app.main:app --reload
```

**Structure:**
```
my-project/
├── app/                    # Application code
│   ├── main.py            # FastAPI app
│   ├── database.py        # DB config
│   ├── models.py          # SQLAlchemy models
│   ├── schemas.py         # Pydantic schemas
│   ├── dependencies.py    # Dependency injection
│   └── routers/           # API routes
├── tests/                 # Pytest tests
├── alembic/               # DB migrations
├── docker-compose.yml     # Multi-container setup
└── requirements.txt       # Dependencies
```

## Core FastAPI Patterns

Quick reference for essential patterns. For detailed explanations, see `references/core-patterns.md`.

### Path Operations

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items")          # GET - retrieve
async def list_items():
    return []

@app.post("/items")         # POST - create
async def create_item(item: dict):
    return item

@app.put("/items/{id}")     # PUT - full update
async def update_item(id: int, item: dict):
    return item

@app.delete("/items/{id}")  # DELETE - remove
async def delete_item(id: int):
    return {"deleted": id}
```

### Request/Response Models

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float

@app.post("/items", response_model=Item)
async def create_item(item: Item):
    return item  # Auto-validated and serialized
```

### Dependency Injection

```python
from fastapi import Depends

def get_db():
    db = Database()
    try:
        yield db
    finally:
        db.close()

@app.get("/items")
async def list_items(db = Depends(get_db)):
    return db.query_items()
```

📚 **Learn More:** `references/core-patterns.md` for path parameters, query parameters, validation, error handling, and more.

## Common Workflows

### 1. Start a New Project

**Simple API (no database):**
```bash
cp -r assets/hello-world/* ./my-api/
cd my-api
uv run uvicorn main:app --reload
```

**Database-backed API:**
```bash
cp -r assets/crud-postgres/* ./my-api/
cd my-api
docker-compose up -d
docker-compose exec app alembic upgrade head
```

### 2. Add Database Integration

Already have a FastAPI project? Add PostgreSQL:

1. Install dependencies: `sqlalchemy`, `asyncpg`, `alembic`
2. Create `database.py` (see `crud-postgres/app/database.py`)
3. Create models in `models.py`
4. Create Pydantic schemas in `schemas.py`
5. Initialize Alembic: `alembic init alembic`
6. Configure Alembic (see `references/database.md`)
7. Create migration: `alembic revision --autogenerate -m "Initial"`
8. Apply migration: `alembic upgrade head`

📚 **Learn More:** `references/database.md` for PostgreSQL, SQLite, MongoDB patterns, connection pooling, and transactions.

### 3. Add Authentication

Add JWT-based authentication:

1. Install dependencies: `python-jose`, `passlib`, `python-multipart`
2. Create auth utilities (password hashing, JWT tokens)
3. Create User model and schemas
4. Implement registration and login endpoints
5. Create `get_current_user` dependency
6. Protect routes with `Depends(get_current_user)`

📚 **Learn More:** `references/authentication.md` for complete JWT setup, OAuth2, RBAC, and security best practices.

### 4. Add Tests

Set up pytest for your FastAPI app:

1. Install: `pytest`, `pytest-asyncio`, `httpx`
2. Create `tests/conftest.py` with test database fixture
3. Write tests using `TestClient`
4. Run: `pytest --cov=app`

📚 **Learn More:** `references/testing.md` for test patterns, mocking, async tests, and fixtures.

### 5. Deploy with Docker

**Single container:**
```bash
docker build -t my-api .
docker run -p 8000:8000 my-api
```

**Multi-container with database:**
```bash
docker-compose up -d
```

📚 **Learn More:** `references/deployment.md` for Docker best practices, Docker Compose, Kubernetes, and production checklists.

## Quick Reference

### Installation

```bash
# With pip
pip install fastapi uvicorn sqlalchemy asyncpg alembic

# With uv (recommended)
uv add fastapi uvicorn sqlalchemy asyncpg alembic
```

### Run Application

```bash
# Development (auto-reload)
uvicorn main:app --reload

# With uv
uv run uvicorn main:app --reload

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app --cov-report=html
```

## Reference Documentation

Detailed guides for specific topics:

### Core FastAPI Concepts
📄 **`references/core-patterns.md`**
- Path operations (GET, POST, PUT, DELETE)
- Request/response models with Pydantic
- Path, query, and body parameters
- Dependency injection
- Environment configuration with pydantic-settings
- Validation and error handling
- Response models and status codes

### Database Integration
📄 **`references/database.md`**
- **PostgreSQL** (primary focus)
  - SQLAlchemy 2.0 async patterns
  - SQLModel patterns (simpler, for learning)
  - Connection pooling
  - Session management
  - Model separation (TaskDB, TaskCreate, TaskUpdate, TaskPublic)
  - CRUD operations
  - Filtering queries
  - Alembic migrations
- **SQLite** for simple projects
- **MongoDB** with Motor/Beanie
- Common patterns: pagination, filtering, transactions

### Authentication & Security
📄 **`references/authentication.md`**
- JWT tokens (primary approach)
- OAuth2 with Password flow
- Password hashing with bcrypt
- Protecting routes
- User registration and login
- Role-based access control (RBAC)
- Refresh tokens
- Security best practices

### Testing
📄 **`references/testing.md`**
- pytest setup and structure
- TestClient for API testing
- Mocking databases
- Async test patterns
- Test fixtures
- Coverage reporting
- Test database patterns

### Deployment
📄 **`references/deployment.md`**
- **Local Development**
  - Running with uvicorn
  - Environment management
- **Docker**
  - Dockerfile best practices
  - Multi-stage builds
- **Docker Compose**
  - Multi-container applications
  - Database + app setup
- **Kubernetes** (reference only)
  - Basic manifests
  - Deployments, Services, ConfigMaps
- Production best practices and checklists

## Code Principles

When generating FastAPI code, always follow these principles:

### 1. Type Hints Everywhere
Always use explicit type hints for all parameters:

**Path Parameters:**
```python
# ✓ GOOD - Explicit type hint
@app.get("/items/{item_id}")
async def get_item(item_id: int):
    return {"id": item_id}

# ✗ BAD - No type hint
@app.get("/items/{item_id}")
async def get_item(item_id):
    return {"id": item_id}
```

**Query Parameters:**
```python
from fastapi import Query

# ✓ GOOD - Type hints with Query validator
@app.get("/search")
async def search(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=100)
):
    return {"query": query, "limit": limit}

# ✗ BAD - Missing type hints
@app.get("/search")
async def search(query, limit=10):
    return {"query": query, "limit": limit}
```

**All Parameters Need Types:**
- Path parameters: `item_id: int`, `username: str`
- Query parameters: `skip: int = 0`, `limit: int = Query(10)`
- Request bodies: `item: Item` (Pydantic model)
- Dependencies: `db: Session = Depends(get_db)`
- Return types: `-> dict`, `-> List[Item]`

### 2. Always Return Dictionaries

DELETE endpoints must return dictionaries, not None:

```python
# ✓ GOOD - Returns dictionary
@app.delete("/items/{item_id}", status_code=200)
async def delete_item(item_id: int):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    del items_db[item_id]
    return {"message": "Item deleted successfully", "id": item_id}

# ✗ BAD - Returns None
@app.delete("/items/{item_id}", status_code=204)
async def delete_item(item_id: int):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    del items_db[item_id]
    return None  # ✗ Don't do this
```

**Status Code Choice:**
- Use `status_code=200` with response body for deletes
- Use `status_code=204` only if truly returning no content (rare)
- **Prefer 200 with confirmation message** for better API clarity

### 3. Descriptive Function Names

Function names should clearly describe what the endpoint does:

```python
# ✓ GOOD - Clear, descriptive names matching purpose
@app.get("/items")
async def list_items():  # Lists all items
    return items_db

@app.get("/items/{item_id}")
async def get_item(item_id: int):  # Gets single item
    return items_db[item_id]

@app.post("/items")
async def create_item(item: Item):  # Creates new item
    return created_item

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):  # Updates existing item
    return updated_item

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):  # Deletes item
    return {"message": "deleted"}

@app.get("/search")
async def search_items(query: str):  # Searches items
    return search_results

# ✗ BAD - Generic or misleading names
@app.get("/items")
async def endpoint1():  # ✗ Not descriptive

@app.post("/items")
async def handle_post():  # ✗ Too generic

@app.get("/search")
async def get_data(q: str):  # ✗ Doesn't indicate search purpose
```

**Naming Convention:**
- `list_*` for GET endpoints returning multiple items
- `get_*` for GET endpoints returning single item
- `create_*` for POST endpoints
- `update_*` for PUT/PATCH endpoints
- `delete_*` or `remove_*` for DELETE endpoints
- `search_*` for search/query endpoints
- Use verb + noun pattern: `get_item`, `create_user`, `search_tasks`

### 4. Complete Error Handling

Always validate and provide clear error messages:

```python
# ✓ GOOD - Comprehensive error handling
@app.get("/tasks/{task_id}")
async def get_task(task_id: int):
    if task_id not in tasks_db:
        raise HTTPException(
            status_code=404,
            detail=f"Task with id {task_id} not found"
        )
    return {"id": task_id, **tasks_db[task_id]}

# ✗ BAD - No validation
@app.get("/tasks/{task_id}")
async def get_task(task_id: int):
    return tasks_db[task_id]  # ✗ Will crash if not found
```

### 5. Response Models

Always specify response_model for type safety and documentation:

```python
# ✓ GOOD - With response model
@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    return item

# ✗ BAD - No response model
@app.get("/items/{item_id}")
async def get_item(item_id: int):
    return item
```

### Summary Checklist

Before considering code complete, verify:
- [ ] All parameters have explicit type hints
- [ ] All endpoints return dictionaries (or Pydantic models)
- [ ] Function names clearly describe endpoint purpose
- [ ] Error cases are handled with HTTPException
- [ ] Response models are specified
- [ ] Query parameters use Query() for validation
- [ ] Status codes match REST conventions (200, 201, 404, etc.)

## Tips for Success

### Use Async When Possible
FastAPI is built for async. Use `async def` for I/O operations (database queries, external APIs).

### Validate Everything
Use Pydantic models for all requests and responses. Automatic validation prevents many bugs.

### Use Dependency Injection
Share logic across endpoints with dependencies. Great for database sessions, authentication, and common parameters.

### Structure Your Project
For applications > 100 lines, use the `crud-postgres` structure:
- Separate models, schemas, and routers
- Keep business logic in separate modules
- Use dependency injection

### Test Your APIs
Write tests for your endpoints. Use TestClient and mock databases for fast, isolated tests.

### Use Docker for Deployment
Docker ensures consistency across environments. Docker Compose simplifies multi-container apps.

### Follow Security Best Practices
- Never commit secrets to git
- Use environment variables for configuration
- Hash passwords with bcrypt
- Use HTTPS in production
- Set appropriate CORS policies

## Troubleshooting

**Import errors when using templates:**
- For `crud-postgres`, run from project root with `PYTHONPATH=.`
- Or use: `uvicorn app.main:app --reload`

**Database connection errors:**
- Check DATABASE_URL in environment
- Ensure PostgreSQL is running
- Verify credentials

**Migration conflicts:**
- Run `alembic downgrade -1` then `alembic upgrade head`
- Or reset: `alembic downgrade base && alembic upgrade head`

**Docker issues:**
- Check logs: `docker-compose logs -f`
- Rebuild: `docker-compose up -d --build`
- Fresh start: `docker-compose down -v && docker-compose up -d`

## Next Steps

After setting up your FastAPI project:

1. **Add More Models:** Extend your database schema
2. **Implement Authentication:** Secure your API endpoints
3. **Add Background Tasks:** Use Celery or FastAPI Background Tasks
4. **Implement Caching:** Add Redis for performance
5. **Set Up Monitoring:** Logging, metrics, and alerts
6. **Deploy to Production:** Cloud platforms (AWS, GCP, Azure, DigitalOcean)

## Additional Resources

- **FastAPI Official Docs:** https://fastapi.tiangolo.com/
- **SQLAlchemy Docs:** https://docs.sqlalchemy.org/
- **Pydantic Docs:** https://docs.pydantic.dev/
- **Alembic Docs:** https://alembic.sqlalchemy.org/
- **Docker Docs:** https://docs.docker.com/

---

**Templates Location:** `assets/hello-world/` and `assets/crud-postgres/`

**Reference Files:** All reference documentation is in the `references/` directory.
