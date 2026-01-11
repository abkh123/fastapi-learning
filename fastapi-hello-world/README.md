# Hands-on Skills for FastAPI

A comprehensive learning resource for building FastAPI applications, from hello-world to production-ready APIs with dependency injection and SQLModel database patterns.

## Contents

- **Core Patterns**: Dependency injection, caching, testing overrides
- **Database Integration**: SQLModel with PostgreSQL, connection pooling, model separation
- **Project Templates**: Hello World, CRUD + PostgreSQL
- **Code Principles**: Type hints, error handling, response models
- **Reference Documentation**: Database, authentication, testing, deployment

## FastAPI Builder Skill Development

This repository documents the sequential development of the **fastapi-builder skill**, covering all patterns learned from basics to production.

### Skill Development Timeline

| Step | Pattern Added | Status |
|------|---------------|--------|
| 1 | Basic dependency injection | ✅ Complete |
| 2 | Chained dependencies | ✅ Complete |
| 3 | Class-based dependencies | ✅ Complete |
| 4 | Dependency caching | ✅ Complete |
| 5 | Testing with overrides | ✅ Complete |
| 6 | Environment configuration | ✅ Complete |
| 7 | SQLModel patterns | ✅ Complete |

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

## Environment Configuration

### Settings with pydantic-settings

```python
# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "My API"
    debug: bool = False
    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### .env File Setup

**`.env.example`** (committed to git):
```bash
APP_NAME=My API
DEBUG=false
DATABASE_URL=postgresql://user:password@host:5432/dbname
SECRET_KEY=generate-with:openssl rand -hex 32
```

**`.env`** (NOT committed):
```bash
APP_NAME=My API
DEBUG=true
DATABASE_URL=postgresql://localhost:5432/dev_db
SECRET_KEY=development-secret-key
```

### Development vs Production

| Aspect | Development | Production |
|--------|-------------|------------|
| Config source | `.env` file | Environment variables |
| Debug mode | `DEBUG=true` | `DEBUG=false` |

**Railway:**
```bash
railway variables set DATABASE_URL=postgresql://...
```

**Fly.io:**
```bash
flyctl secrets set DATABASE_URL=postgresql://...
```

## SQLModel Database Integration

### Database Configuration with Connection Pooling

**database.py:**

```python
from sqlmodel import SQLModel, create_engine, Session
from config import get_settings
from models import TaskDB

settings = get_settings()

# Create engine with connection pooling
engine = create_engine(
    settings.database_url,
    echo=False,
    pool_size=10,           # Number of connections to maintain
    max_overflow=20,         # Additional connections beyond pool_size
    pool_pre_ping=True,      # Test connections before using
    pool_recycle=3600,       # Recycle connections after 1 hour
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
```

### Model Separation Pattern

**models.py:**

```python
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone


# Database model (table=True)
class TaskDB(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    status: str = Field(default="pending")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Request: Create (no id, no created_at)
class TaskCreate(SQLModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    status: str = Field(default="pending")


# Request: Update (all optional, no id/created_at)
class TaskUpdate(SQLModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = None


# Response: What clients see
class TaskPublic(SQLModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    created_at: datetime
```

### CRUD Operations

**main.py:**

```python
from typing import List
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select
from models import TaskDB, TaskCreate, TaskUpdate, TaskPublic
from database import get_session

app = FastAPI()


# Create
@app.post("/tasks", status_code=201, response_model=TaskPublic)
def create_task(task: TaskCreate, session: Session = Depends(get_session)) -> TaskPublic:
    db_task = TaskDB.model_validate(task)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return TaskPublic.model_validate(db_task)


# Read all
@app.get("/tasks", response_model=List[TaskPublic])
def list_tasks(session: Session = Depends(get_session)) -> List[TaskPublic]:
    tasks = session.exec(select(TaskDB)).all()
    return [TaskPublic.model_validate(task) for task in tasks]


# Read one
@app.get("/tasks/{task_id}", response_model=TaskPublic)
def get_task(task_id: int, session: Session = Depends(get_session)) -> TaskPublic:
    task = session.get(TaskDB, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskPublic.model_validate(task)


# Update (partial)
@app.put("/tasks/{task_id}", response_model=TaskPublic)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    session: Session = Depends(get_session)
) -> TaskPublic:
    task = session.get(TaskDB, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    session.add(task)
    session.commit()
    session.refresh(task)
    return TaskPublic.model_validate(task)


# Delete
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, session: Session = Depends(get_session)) -> dict:
    task = session.get(TaskDB, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    session.delete(task)
    session.commit()
    return {"message": "Task deleted successfully", "task_id": task_id}
```

### Filtering

```python
from datetime import timedelta, timezone

@app.get("/tasks/by-status/{status}", response_model=List[TaskPublic])
def filter_by_status(status: str, session: Session = Depends(get_session)):
    statement = select(TaskDB).where(TaskDB.status == status)
    tasks = session.exec(statement).all()
    return [TaskPublic.model_validate(task) for task in tasks]

@app.get("/tasks/recent", response_model=List[TaskPublic])
def recent_tasks(days: int = 7, session: Session = Depends(get_session)):
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    statement = select(TaskDB).where(TaskDB.created_at >= cutoff_date)
    tasks = session.exec(statement).all()
    return [TaskPublic.model_validate(task) for task in tasks]
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
1. **Path operations**: GET, POST, PUT, DELETE
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

### Level 4: Database with SQLModel
1. **Model separation**: TaskDB, TaskCreate, TaskUpdate, TaskPublic
2. **CRUD operations**: Create, Read, Update, Delete
3. **Filtering queries**: `where()` clauses with `select()`
4. **Connection pooling**: `pool_size`, `max_overflow`, `pool_pre_ping`

### Level 5: Production
1. **Environment configuration**: pydantic-settings with .env
2. **Field validation**: `@field_validator` for URLs and secrets
3. **Database migrations**: Alembic for schema changes
4. **Deployment**: Railway, Fly.io, Docker

## Common Workflows

### Add Database to Existing Project

```bash
# Install dependencies
pip install sqlmodel psycopg2-binary

# Create database.py with connection pooling
# Create models.py with TaskDB, TaskCreate, TaskUpdate, TaskPublic
# Update main.py with CRUD endpoints

# Reset database if schema changes
python reset_db.py
```

### Add Tests

```bash
# Install dependencies
pip install pytest pytest-asyncio httpx

# Create test_dep.py with dependency overrides
# Run: pytest test_dep.py -v
```

### Deploy with Connection Pooling

```bash
# Railway
railway variables set DATABASE_URL=postgresql://...

# Fly.io
flyctl secrets set DATABASE_URL=postgresql://...
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
  - `references/core-patterns.md` - Path operations, dependencies, validation, environment config
  - `references/database.md` - SQLAlchemy, SQLModel, Alembic, async patterns
  - `references/authentication.md` - JWT, OAuth2, RBAC
  - `references/testing.md` - pytest, fixtures, mocking
  - `references/deployment.md` - Docker, Docker Compose, Kubernetes

## License

This is a learning resource. Feel free to use and modify as needed.
