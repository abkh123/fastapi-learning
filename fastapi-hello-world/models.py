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
