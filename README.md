# FastAPI Learning Repository

A comprehensive learning resource for building FastAPI applications, from hello-world to production-ready APIs with dependency injection patterns.

## Contents

- **Core Patterns**: Dependency injection, caching, testing overrides
- **Project Templates**: Hello World, CRUD + PostgreSQL
- **Code Principles**: Type hints, error handling, response models
- **Reference Documentation**: Database, authentication, testing, deployment

## Quick Start

### For Beginners

Start with a simple API without a database:

```bash
# Create a new project
mkdir my-fastapi-app
cd my-fastapi-app

# Create main.py
cat > main.py << 'EOF'
from fastapi import FastAPI, Depends
from functools import lru_cache
from typing import Optional

app = FastAPI()

# Config dependency (cached across requests)
@lru_cache
def get_config():
    return {"app_name": "My API", "debug": True}

# Database dependency with cleanup
class Database:
    def __init__(self):
        self.items = {}

def get_db():
    db = Database()
    try:
        yield db
    finally:
        pass  # Cleanup logic here

@app.get("/")
def read_root(config: dict = Depends(get_config)):
    return {"message": f"Welcome to {config['app_name']}"}

@app.get("/items")
def list_items(db = Depends(get_db)):
    return db.items
EOF

# Run the application
uv run uvicorn main:app --reload
# Visit http://localhost:8000/docs
```

### For Production Applications

Use the CRUD + PostgreSQL template:

```bash
# Copy the template
cp -r claude-code-skills-lab-main/.claude/skills/fastapi-builder/assets/crud-postgres/* ./my-api/
cd my-api

# Run with Docker Compose (easiest)
docker-compose up -d
docker-compose exec app alembic upgrade head
```

## Dependency Injection Patterns

### 1. Basic Dependency

```python
from fastapi import Depends

def get_db():
    db = Database()
    try:
        yield db
    finally:
        db.close()

@app.get("/items")
def list_items(db = Depends(get_db)):
    return db.query_items()
```

### 2. Chained Dependencies

```python
def get_config():
    return {"app_name": "My API", "log_level": "INFO"}

def get_logger(config: dict = Depends(get_config)):
    return logging.getLogger(config["app_name"])

@app.get("/logs")
def get_logs(logger = Depends(get_logger)):
    return {"logger_name": logger.name}
```

### 3. Class-based Dependencies

```python
class TaskService:
    def __init__(self, config: dict = Depends(get_config)):
        self.config = config
        self._tasks = {}

    def list(self):
        return list(self._tasks.values())

    def create(self, task_data):
        task_id = len(self._tasks) + 1
        self._tasks[task_id] = task_data
        return task_data

@app.get("/tasks")
def list_tasks(service: TaskService = Depends(TaskService)):
    return service.list()
```

### 4. Dependency Caching

```python
from functools import lru_cache

# Cached across requests - same instance for all requests
@lru_cache
def get_config():
    return Settings(app_name="My API", debug=True)

# Per-request caching - same instance within one request
def get_db():
    db = Database()
    try:
        yield db
    finally:
        db.close()

# Disable caching - new instance each time
@app.get("/items")
def get_items(db1 = Depends(get_db, use_cache=False), db2 = Depends(get_db, use_cache=False)):
    # db1 and db2 are DIFFERENT instances
    return {"db1_id": id(db1), "db2_id": id(db2)}
```

### 5. Testing with Dependency Overrides

```python
# test_dep.py
import pytest
from httpx import AsyncClient, ASGITransport
from main import app, get_config

def get_test_config():
    return Settings(app_name="Test API", debug=True)

@pytest_asyncio.fixture
async def test_client():
    # Override dependency before test
    app.dependency_overrides[get_config] = get_test_config

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    # Clean up after test
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_config_override(test_client):
    response = await test_client.get("/config")
    assert response.json()["app_name"] == "Test API"
```

## Code Principles

### 1. Type Hints Everywhere

```python
# ✓ GOOD
@app.get("/items/{item_id}")
async def get_item(item_id: int) -> dict:
    return {"id": item_id}

# ✗ BAD
@app.get("/items/{item_id}")
async def get_item(item_id):
    return {"id": item_id}
```

### 2. Descriptive Function Names

```python
# ✓ GOOD
@app.get("/items")
async def list_items(): ...

@app.get("/items/{item_id}")
async def get_item(item_id: int): ...

@app.post("/items")
async def create_item(item: Item): ...

# ✗ BAD
@app.get("/items")
async def endpoint1(): ...

@app.post("/items")
async def handle_post(): ...
```

### 3. Complete Error Handling

```python
# ✓ GOOD
@app.get("/tasks/{task_id}")
async def get_task(task_id: int):
    if task_id not in tasks_db:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )
    return tasks_db[task_id]

# ✗ BAD
@app.get("/tasks/{task_id}")
async def get_task(task_id: int):
    return tasks_db[task_id]  # Will crash if not found
```

### 4. Response Models

```python
# ✓ GOOD
@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    return item

# ✗ BAD
@app.get("/items/{item_id}")
async def get_item(item_id: int):
    return item
```

## Learning Path

### Level 1: Fundamentals
1. **Understand path operations**: GET, POST, PUT, DELETE
2. **Pydantic models**: Request/response validation
3. **Path and query parameters**: Type conversion
4. **Basic dependencies**: Simple function dependencies

### Level 2: Dependency Injection
1. **Yield for cleanup**: Resource management
2. **Chained dependencies**: One dependency depending on another
3. **Class-based dependencies**: Service classes with `__init__`
4. **Dependency caching**: `@lru_cache` and `use_cache=False`

### Level 3: Testing
1. **Dependency overrides**: `app.dependency_overrides` for testing
2. **Test fixtures**: pytest setup with `@pytest_asyncio.fixture`
3. **Async test patterns**: Testing async endpoints

### Level 4: Production
1. **Database integration**: SQLAlchemy async with PostgreSQL
2. **Authentication**: JWT tokens, OAuth2
3. **Deployment**: Docker, Docker Compose
4. **Best practices**: Security, CORS, environment variables

## Common Workflows

### Add Database to Existing Project

```bash
# Install dependencies
pip install sqlalchemy asyncpg alembic

# Create database.py
# Create models.py
# Create schemas.py

# Initialize Alembic
alembic init alembic

# Create and apply migration
alembic revision --autogenerate -m "Initial"
alembic upgrade head
```

### Add Authentication

```bash
# Install dependencies
pip install python-jose passlib python-multipart

# Create auth utilities (password hashing, JWT tokens)
# Create User model and schemas
# Implement registration and login endpoints
# Create get_current_user dependency
# Protect routes with Depends(get_current_user)
```

### Add Tests

```bash
# Install dependencies
pip install pytest pytest-asyncio httpx

# Create tests/conftest.py with test database fixture
# Write tests using TestClient
# Run: pytest --cov=app
```

### Deploy with Docker

```bash
# Single container
docker build -t my-api .
docker run -p 8000:8000 my-api

# Multi-container with database
docker-compose up -d
```

## Requirements

- Python 3.11+
- uv package manager (recommended) or pip
- Docker (optional, for containerization)
- PostgreSQL (for CRUD template)

## Skill Documentation

The FastAPI Builder skill provides:

- **Templates**: `assets/hello-world/`, `assets/crud-postgres/`
- **References**:
  - `references/core-patterns.md` - Path operations, dependencies, validation
  - `references/database.md` - SQLAlchemy, Alembic, async patterns
  - `references/authentication.md` - JWT, OAuth2, RBAC
  - `references/testing.md` - pytest, fixtures, mocking
  - `references/deployment.md` - Docker, Docker Compose, Kubernetes

## License

This is a learning resource. Feel free to use and modify as needed.
