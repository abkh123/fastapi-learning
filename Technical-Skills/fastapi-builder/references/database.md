# Database Integration

Patterns for integrating SQL and NoSQL databases with FastAPI.

## PostgreSQL with SQLAlchemy 2.0

PostgreSQL is the recommended production database. Use SQLAlchemy 2.0 with async support.

### Installation

```bash
pip install sqlalchemy asyncpg psycopg2-binary alembic
# or with uv
uv add sqlalchemy asyncpg psycopg2-binary alembic
```

### Database Configuration

**database.py:**

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os

# Database URL format: postgresql+asyncpg://user:password@host:port/database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/mydb"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Log SQL queries (disable in production)
    future=True,
    pool_size=10,  # Connection pool size
    max_overflow=20  # Additional connections when pool is full
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
class Base(DeclarativeBase):
    pass

# Dependency for getting DB session
async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### Models

**models.py:**

```python
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship
    items: Mapped[list["Item"]] = relationship("Item", back_populates="owner")

class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    price: Mapped[float] = mapped_column(Float)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))

    # Relationship
    owner: Mapped["User"] = relationship("User", back_populates="items")
```

### Schemas (Pydantic Models)

**schemas.py:**

```python
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ItemBase(BaseModel):
    name: str
    description: str | None = None
    price: float

class ItemCreate(ItemBase):
    pass

class ItemResponse(ItemBase):
    id: int
    owner_id: int

    model_config = ConfigDict(from_attributes=True)
```

### CRUD Operations

**crud.py:**

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models import User, Item
from schemas import UserCreate, ItemCreate

# Create
async def create_user(db: AsyncSession, user: UserCreate):
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hash_password(user.password)
    )
    db.add(db_user)
    await db.flush()  # Get the ID without committing
    await db.refresh(db_user)
    return db_user

# Read one
async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()

# Read many
async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(User).offset(skip).limit(limit)
    )
    return result.scalars().all()

# Update
async def update_user(db: AsyncSession, user_id: int, updates: dict):
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user:
        for key, value in updates.items():
            setattr(user, key, value)
        await db.flush()
        await db.refresh(user)
    return user

# Delete
async def delete_user(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user:
        await db.delete(user)
    return user

# Read with relationships (eager loading)
async def get_user_with_items(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(User)
        .options(selectinload(User.items))
        .where(User.id == user_id)
    )
    return result.scalar_one_or_none()
```

### API Endpoints

**routers/users.py:**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
import crud
import schemas

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_user(db, user)

@router.get("/{user_id}", response_model=schemas.UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/", response_model=list[schemas.UserResponse])
async def list_users(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.get_users(db, skip, limit)
```

### Database Migrations with Alembic

**Initialize Alembic:**

```bash
alembic init alembic
```

**alembic/env.py (configure for async):**

```python
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from database import Base
import models  # Import all models

config = context.config
target_metadata = Base.metadata

def run_migrations_online():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()
```

**Create and apply migrations:**

```bash
# Create migration
alembic revision --autogenerate -m "Create users and items tables"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## SQLModel

SQLModel combines Pydantic and SQLAlchemy for simpler FastAPI databases. Great for learning and small-to-medium applications.

### Installation

```bash
pip install sqlmodel psycopg2-binary
# or with uv
uv add sqlmodel psycopg2-binary
```

### Database Configuration

**database.py:**

```python
from sqlmodel import SQLModel, create_engine, Session
from config import get_settings
from models import TaskDB  # Import so metadata is registered

settings = get_settings()

# Create engine with connection pooling
engine = create_engine(
    settings.database_url,
    echo=False,
    # Pool settings for PostgreSQL
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

Separate database models from API models for better control:

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

### SQLModel vs SQLAlchemy

| Feature | SQLModel | SQLAlchemy 2.0 |
|---------|---------|----------------|
| **Best for** | Learning, prototypes, small apps | Production, complex queries |
| **Code** | Less code, Pydantic integrated | More verbose, separate schemas |
| **Async** | Requires separate setup | Native async support |
| **Type hints** | Built-in Pydantic validation | Separate Pydantic schemas needed |

---

## SQLite

SQLite is great for development and small applications. No server setup required.

### Configuration

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# SQLite database file
DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# Create tables
Base.metadata.create_all(bind=engine)
```

### Synchronous CRUD (SQLite)

```python
from sqlalchemy.orm import Session

def create_user(db: Session, user: UserCreate):
    db_user = User(**user.model_dump())
    db.add(db_user)
    db.flush()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()
```

**When to use SQLite:**
- Development and testing
- Small applications (< 100k rows)
- Single-user applications
- Prototyping

**When NOT to use SQLite:**
- Production with multiple concurrent writers
- High traffic applications
- Applications requiring complex queries

---

## MongoDB with Motor/Beanie

MongoDB is a NoSQL document database. Use Beanie (ODM built on Motor and Pydantic).

### Installation

```bash
pip install beanie motor
# or with uv
uv add beanie motor
```

### Configuration

**database.py:**

```python
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from models import User, Item
import os

DATABASE_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = "mydb"

async def init_db():
    client = AsyncIOMotorClient(DATABASE_URL)
    await init_beanie(
        database=client[DATABASE_NAME],
        document_models=[User, Item]
    )
```

### Models (Beanie Documents)

**models.py:**

```python
from beanie import Document, Link
from pydantic import EmailStr, Field
from datetime import datetime
from typing import Optional

class User(Document):
    email: EmailStr
    username: str
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"  # Collection name
        indexes = ["email", "username"]

class Item(Document):
    name: str
    description: Optional[str] = None
    price: float
    owner: Link[User]  # Reference to User

    class Settings:
        name = "items"
```

### CRUD Operations (MongoDB)

```python
from models import User, Item
from beanie import PydanticObjectId

# Create
async def create_user(user_data: dict):
    user = User(**user_data)
    await user.insert()
    return user

# Read one
async def get_user(user_id: PydanticObjectId):
    return await User.get(user_id)

# Read many
async def get_users(skip: int = 0, limit: int = 100):
    return await User.find_all().skip(skip).limit(limit).to_list()

# Find by field
async def get_user_by_email(email: str):
    return await User.find_one(User.email == email)

# Update
async def update_user(user_id: PydanticObjectId, updates: dict):
    user = await User.get(user_id)
    if user:
        await user.update({"$set": updates})
    return user

# Delete
async def delete_user(user_id: PydanticObjectId):
    user = await User.get(user_id)
    if user:
        await user.delete()
    return user
```

### Startup Event

**main.py:**

```python
from fastapi import FastAPI
from database import init_db

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await init_db()
```

---

## Common Patterns

### Pagination

```python
from fastapi import Query

@app.get("/items")
async def list_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    items = await crud.get_items(db, skip=skip, limit=limit)
    total = await crud.count_items(db)
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }
```

### Filtering

```python
from sqlalchemy import select

async def get_items_by_filter(
    db: AsyncSession,
    min_price: float | None = None,
    max_price: float | None = None,
    owner_id: int | None = None
):
    query = select(Item)

    if min_price is not None:
        query = query.where(Item.price >= min_price)
    if max_price is not None:
        query = query.where(Item.price <= max_price)
    if owner_id is not None:
        query = query.where(Item.owner_id == owner_id)

    result = await db.execute(query)
    return result.scalars().all()
```

### Transactions

```python
async def transfer_item(
    db: AsyncSession,
    item_id: int,
    from_user_id: int,
    to_user_id: int
):
    async with db.begin():  # Transaction
        item = await get_item(db, item_id)
        if item.owner_id != from_user_id:
            raise ValueError("Item does not belong to user")

        item.owner_id = to_user_id
        await db.flush()

    return item
```

### Connection Pooling (PostgreSQL)

```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,        # Number of connections to keep open
    max_overflow=20,     # Additional connections when pool is full
    pool_timeout=30,     # Seconds to wait for connection
    pool_recycle=3600,   # Recycle connections after 1 hour
    pool_pre_ping=True   # Test connections before using
)
```

---

## Best Practices

1. **Use async for I/O operations** - Better performance with async database drivers
2. **Always use connection pooling** - Don't create new connections per request
3. **Close sessions properly** - Use dependency injection with try/finally
4. **Use migrations** - Never modify production database schema manually
5. **Index frequently queried fields** - Especially foreign keys and search fields
6. **Validate data at API layer** - Use Pydantic models for validation
7. **Use transactions for multi-step operations** - Ensure data consistency
8. **Separate models and schemas** - SQLAlchemy models ≠ Pydantic schemas

## Learn More

- **Authentication:** See `references/authentication.md` for user authentication with databases
- **Testing:** See `references/testing.md` for testing with databases
- **Deployment:** See `references/deployment.md` for database deployment with Docker
