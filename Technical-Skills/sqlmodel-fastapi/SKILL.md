---
name: sqlmodel-fastapi
description: Database design and management using SQLModel with FastAPI. Use when creating database models, implementing CRUD operations, setting up model separation patterns (DB/Create/Update/Public), configuring connection pooling, managing relationships, or working with Alembic migrations in FastAPI applications.
---

# SQLModel with FastAPI

Database design and management using SQLModel for FastAPI applications: model separation, CRUD operations, connection pooling, relationships, and migrations.

## Quick Start

### Installation

```bash
pip install sqlmodel psycopg2-binary
# or with uv
uv add sqlmodel psycopg2-binary
```

### Basic Setup

```python
from sqlmodel import SQLModel, create_engine, Session

# Database URL: postgresql://user:password@host:port/database
DATABASE_URL = "postgresql://user:pass@localhost:5432/mydb"

engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
```

## Model Separation Pattern

Use separate SQLModel classes for different purposes:

| Model | Purpose | `table=True` |
|-------|---------|--------------|
| **TaskDB** | Database table | Yes |
| **TaskCreate** | Create request | No |
| **TaskUpdate** | Update request | No |
| **TaskPublic** | API response | No |

### Example Models

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

## CRUD Operations

### Create

```python
from fastapi import Depends
from sqlmodel import Session

@app.post("/tasks", status_code=201, response_model=TaskPublic)
def create_task(task: TaskCreate, session: Session = Depends(get_session)):
    db_task = TaskDB.model_validate(task)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return TaskPublic.model_validate(db_task)
```

### Read All

```python
from typing import List

@app.get("/tasks", response_model=List[TaskPublic])
def list_tasks(session: Session = Depends(get_session)):
    tasks = session.exec(select(TaskDB)).all()
    return [TaskPublic.model_validate(task) for task in tasks]
```

### Read One

```python
from fastapi import HTTPException

@app.get("/tasks/{task_id}", response_model=TaskPublic)
def get_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(TaskDB, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskPublic.model_validate(task)
```

### Update (Partial)

```python
@app.put("/tasks/{task_id}", response_model=TaskPublic)
def update_task(task_id: int, task_update: TaskUpdate, session: Session = Depends(get_session)):
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
```

### Delete

```python
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(TaskDB, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    session.delete(task)
    session.commit()
    return {"message": "Task deleted successfully", "task_id": task_id}
```

## Database Configuration

### Connection Pooling

```python
engine = create_engine(
    DATABASE_URL,
    echo=False,
    # Pool settings for PostgreSQL
    pool_size=10,           # Number of connections to maintain
    max_overflow=20,         # Additional connections beyond pool_size
    pool_pre_ping=True,      # Test connections before using
    pool_recycle=3600,       # Recycle connections after 1 hour
)
```

### database.py Complete Example

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

## Filtering and Queries

### Basic Filter

```python
from sqlmodel import select

@app.get("/tasks/by-status/{status}")
def filter_by_status(status: str, session: Session = Depends(get_session)):
    statement = select(TaskDB).where(TaskDB.status == status)
    tasks = session.exec(statement).all()
    return [TaskPublic.model_validate(task) for task in tasks]
```

### Date Range Filter

```python
from datetime import timedelta, timezone

@app.get("/tasks/recent")
def recent_tasks(days: int = 7, session: Session = Depends(get_session)):
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    statement = select(TaskDB).where(TaskDB.created_at >= cutoff_date)
    tasks = session.exec(statement).all()
    return [TaskPublic.model_validate(task) for task in tasks]
```

### Multi-Option Filter

```python
from typing import Optional
from fastapi import Query

@app.get("/tasks/search")
def search_tasks(
    status: Optional[str] = None,
    title_contains: Optional[str] = None,
    days: Optional[int] = None,
    session: Session = Depends(get_session)
):
    statement = select(TaskDB)

    if status:
        statement = statement.where(TaskDB.status == status)
    if title_contains:
        statement = statement.where(TaskDB.title.contains(title_contains))
    if days:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        statement = statement.where(TaskDB.created_at >= cutoff_date)

    tasks = session.exec(statement).all()
    return [TaskPublic.model_validate(task) for task in tasks]
```

## Relationships

### One-to-Many

```python
from sqlmodel import Field, Relationship
from typing import List, Optional

class UserDB(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    items: List["ItemDB"] = Relationship(back_populates="owner")

class ItemDB(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    owner_id: int = Field(foreign_key="userdb.id")
    owner: UserDB = Relationship(back_populates="items")
```

### Many-to-Many

```python
from sqlmodel import Link

class UserTeamLink(SQLModel, table=True):
    user_id: int = Field(foreign_key="userdb.id", primary_key=True)
    team_id: int = Field(foreign_key="teamdb.id", primary_key=True)

class UserDB(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    teams: List["TeamDB"] = Relationship(back_populates="users", link_model=UserTeamLink)

class TeamDB(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    users: List["UserDB"] = Relationship(back_populates="teams", link_model=UserTeamLink)
```

### Query with Relationships

```python
from sqlmodel import selectinload

def get_user_with_items(user_id: int, session: Session):
    statement = select(UserDB).options(selectinload(UserDB.items)).where(UserDB.id == user_id)
    return session.exec(statement).first()
```

## Migrations with Alembic

### Initialize Alembic

```bash
alembic init alembic
```

### Configure alembic/env.py

```python
from alembic import context
from database import Base
import models

target_metadata = Base.metadata

def run_migrations_online():
    connectable = create_engine(DATABASE_URL)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
```

### Create Migration

```bash
alembic revision --autogenerate -m "Initial migration"
```

### Apply Migration

```bash
alembic upgrade head
```

### Rollback

```bash
alembic downgrade -1
```

## Best Practices

1. **Use model separation** - Prevents clients from setting `id` or `created_at`
2. **Validate with Field()** - Use `min_length`, `max_length`, `default`
3. **Use exclude_unset** - For partial updates with `model_dump(exclude_unset=True)`
4. **Connection pooling** - Configure `pool_size`, `max_overflow`, `pool_pre_ping`
5. **Use timezones** - `datetime.now(timezone.utc)` instead of `datetime.utcnow()`
6. **Filter with select()** - Use `select().where()` not query string
7. **Test with rollback** - Rollback transactions in tests

## Reference Files

For advanced patterns and detailed guides:

- **Model Separation**: See `references/model-separation.md` for comprehensive patterns and examples
- **CRUD Operations**: See `references/crud.md` for all CRUD patterns with error handling
- **Database Configuration**: See `references/database-config.md` for pooling, engines, and sessions
- **Relationships**: See `references/relationships.md` for one-to-many, many-to-many, and querying
- **Migrations**: See `references/migrations.md` for Alembic workflows and migration patterns
- **Filtering**: See `references/filtering.md` for complex queries, pagination, and search
