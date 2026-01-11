# Database Configuration

Complete guide for configuring SQLModel database engines, sessions, and connection pooling.

## Database URL Format

### PostgreSQL

```python
# Format: postgresql://user:password@host:port/database
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/mydb"

# With connection string parameters
DATABASE_URL = "postgresql://user:pass@localhost:5432/mydb?sslmode=require"

# Using environment variable
import os
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/mydb")
```

### SQLite

```python
# File-based database
DATABASE_URL = "sqlite:///./app.db"

# In-memory database (for testing)
DATABASE_URL = "sqlite:///:memory:"
```

## create_engine Options

### Basic Engine

```python
from sqlmodel import create_engine, SQLModel

DATABASE_URL = "postgresql://user:pass@localhost:5432/mydb"
engine = create_engine(DATABASE_URL)
```

### With Connection Pooling

```python
engine = create_engine(
    DATABASE_URL,
    echo=False,              # Log SQL queries (False in production)
    pool_size=10,            # Number of connections to maintain
    max_overflow=20,         # Additional connections when pool is full
    pool_timeout=30,         # Seconds to wait for connection
    pool_recycle=3600,       # Recycle connections after 1 hour
    pool_pre_ping=True,      # Test connections before using
)
```

### Engine Options Explained

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `echo` | False | Log SQL to console (True for debugging) |
| `pool_size` | 5 | Number of persistent connections |
| `max_overflow` | 10 | Max connections beyond pool_size |
| `pool_timeout` | 30 | Seconds to wait before timeout |
| `pool_recycle` | -1 | Recycle connections after N seconds |
| `pool_pre_ping` | False | Test connection before use |

### Development vs Production

**Development:**
```python
engine = create_engine(
    DATABASE_URL,
    echo=True,  # See SQL queries
    pool_size=5,
)
```

**Production:**
```python
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,  # More connections
    max_overflow=40,
    pool_pre_ping=True,  # Detect stale connections
    pool_recycle=3600,  # Recycle every hour
)
```

## Complete database.py

### Basic Version

```python
from sqlmodel import SQLModel, create_engine, Session
from models import TaskDB

DATABASE_URL = "postgresql://user:pass@localhost:5432/mydb"

engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
```

### With Settings

```python
from sqlmodel import SQLModel, create_engine, Session
from config import get_settings
from models import TaskDB

settings = get_settings()

engine = create_engine(
    settings.database_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
```

### With Cleanup

```python
from sqlmodel import SQLModel, create_engine, Session
from contextlib import contextmanager
from typing import Generator

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@contextmanager
def get_session() -> Generator[Session, None, None]:
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

## Session Management

### FastAPI Dependency

```python
from fastapi import Depends
from sqlmodel import Session

@app.get("/tasks")
def list_tasks(session: Session = Depends(get_session)):
    tasks = session.exec(select(TaskDB)).all()
    return tasks
```

### Async Session (AsyncSQLModel)

```python
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/mydb"

engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
```

### Multiple Databases

```python
# Primary database
primary_engine = create_engine("postgresql://localhost/primary")

# Replica database (read-only)
replica_engine = create_engine("postgresql://localhost/replica")

def get_primary_session():
    with Session(primary_engine) as session:
        yield session

def get_replica_session():
    with Session(replica_engine) as session:
        yield session

@app.get("/tasks")  # Read from replica
def list_tasks(session: Session = Depends(get_replica_session)):
    return session.exec(select(TaskDB)).all()

@app.post("/tasks")  # Write to primary
def create_task(task: TaskCreate, session: Session = Depends(get_primary_session)):
    # ... create task
```

## Connection Pool Tuning

### Calculate Pool Size

```
pool_size = (number of workers) × (connections per worker) + (buffer)

Example with 4 workers, 5 connections each:
pool_size = 4 × 5 = 20
max_overflow = 10 (buffer)
Total = 30 connections
```

### Gunicorn/Uvicorn Workers

**Gunicorn:**
```bash
# 4 workers, 2 threads each
gunicorn app:app -w 4 --threads 2

# Pool should be: 4 × 2 = 8 minimum
pool_size = 10
max_overflow = 10
```

**Uvicorn:**
```bash
# Single process
uvicorn app:app

# Pool: 10 connections
pool_size = 10

# Multiple workers
uvicorn app:app --workers 4

# Pool: 4 × 10 = 40 connections needed
pool_size = 40
max_overflow = 20
```

### SQLite Configuration

```python
# SQLite doesn't support connection pooling the same way
engine = create_engine(
    "sqlite:///./app.db",
    connect_args={"check_same_thread": False}  # Required for FastAPI
)
```

## Startup and Shutdown

### Lifespan Events

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_db_and_tables()
    yield
    # Shutdown (optional)
    engine.dispose()

app = FastAPI(lifespan=lifespan)
```

### Event Handlers (Deprecated)

```python
@app.on_event("startup")
async def startup_event():
    create_db_and_tables()

@app.on_event("shutdown")
async def shutdown_event():
    engine.dispose()
```

## Testing Configuration

### Test Database

```python
# conftest.py
import pytest
from sqlmodel import create_engine, Session
from sqlalchemy import text

@pytest.fixture(scope="function")
def test_db():
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    # Drop all tables after test
    SQLModel.metadata.drop_all(engine)
```

### Test with Dependency Override

```python
# test_main.py
from fastapi.testclient import TestClient
from main import app, get_session

def get_test_session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_create_task():
    app.dependency_overrides[get_session] = get_test_session
    client = TestClient(app)

    response = client.post("/tasks", json={"title": "Test"})
    assert response.status_code == 201

    app.dependency_overrides.clear()
```

## Troubleshooting

### Connection Pool Exhausted

**Error:** `sqlalchemy.exc.TimeoutError: QueuePool limit exceeded`

**Solutions:**
1. Increase `pool_size` and `max_overflow`
2. Reduce number of workers
3. Close sessions properly (use `yield` in dependency)
4. Add `pool_recycle` to close stale connections

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_recycle=3600,
    pool_pre_ping=True,
)
```

### Stale Connections

**Error:** `psycopg2.OperationalError: server closed the connection unexpectedly`

**Solution:** Enable `pool_pre_ping` to test connections before use

```python
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Test before using
    pool_recycle=3600,  # Recycle every hour
)
```

### Lock Timeout

**Error:** Database locks during concurrent writes

**Solutions:**
1. Use transactions properly
2. Reduce connection time (yield sessions quickly)
3. Add retry logic

```python
from sqlalchemy.exc import OperationalError
import time

def retry_on_lock(func):
    def wrapper(*args, **kwargs):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except OperationalError as e:
                if "could not acquire lock" in str(e) and attempt < max_retries - 1:
                    time.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                    continue
                raise
    return wrapper
```

## Best Practices

1. **Use environment variables** - Never hardcode DATABASE_URL
2. **Pool pre-ping in production** - Detect stale connections
3. **Set pool_recycle** - Prevent connection leaks
4. **Close sessions properly** - Use yield in dependencies
5. **Separate test database** - Use SQLite for speed
6. **Monitor pool usage** - Log pool statistics
7. **Tune for workers** - Calculate pool size based on workers
8. **Use SSL in production** - `sslmode=require` in connection string
