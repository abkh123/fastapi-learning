from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlmodel import Session, select
from models import TaskDB, TaskCreate, TaskUpdate, TaskPublic
from database import create_db_and_tables, get_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_db_and_tables()
    yield
    # Shutdown (if needed)


app = FastAPI(title="Task API", lifespan=lifespan)


# Create a New Task
@app.post("/tasks", status_code=201, response_model=TaskPublic)
def create_task(task: TaskCreate, session: Session = Depends(get_session)) -> TaskPublic:
    # Convert TaskCreate to TaskDB for database
    db_task = TaskDB.model_validate(task)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return TaskPublic.model_validate(db_task)


# List all tasks
@app.get("/tasks", response_model=List[TaskPublic])
def list_tasks(session: Session = Depends(get_session)) -> List[TaskPublic]:
    tasks = session.exec(select(TaskDB)).all()
    return [TaskPublic.model_validate(task) for task in tasks]


# Get a Single Task
@app.get("/tasks/{task_id}", response_model=TaskPublic)
def get_task(task_id: int, session: Session = Depends(get_session)) -> TaskPublic:
    task = session.get(TaskDB, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskPublic.model_validate(task)


# Update a Single Task
@app.put("/tasks/{task_id}", response_model=TaskPublic)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    session: Session = Depends(get_session)
) -> TaskPublic:
    task = session.get(TaskDB, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Only update fields that were actually provided
    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    session.add(task)
    session.commit()
    session.refresh(task)
    return TaskPublic.model_validate(task)


# Delete a Single Task
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, session: Session = Depends(get_session)) -> dict:
    task = session.get(TaskDB, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    session.delete(task)
    session.commit()
    return {"message": "Task deleted successfully", "task_id": task_id}


# Filter tasks by status
@app.get("/tasks/by-status/{status}", response_model=List[TaskPublic])
def filter_by_status(status: str, session: Session = Depends(get_session)) -> List[TaskPublic]:
    statement = select(TaskDB).where(TaskDB.status == status)
    tasks = session.exec(statement).all()
    return [TaskPublic.model_validate(task) for task in tasks]


# Filter tasks created in last N days
@app.get("/tasks/recent", response_model=List[TaskPublic])
def recent_tasks(
    days: int = Query(7, ge=1, le=365, description="Number of days to look back"),
    session: Session = Depends(get_session)
) -> List[TaskPublic]:
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    statement = select(TaskDB).where(TaskDB.created_at >= cutoff_date)
    tasks = session.exec(statement).all()
    return [TaskPublic.model_validate(task) for task in tasks]


# General filter with multiple options
@app.get("/tasks/search", response_model=List[TaskPublic])
def search_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    title_contains: Optional[str] = Query(None, description="Search in title"),
    days: Optional[int] = Query(None, ge=1, le=365, description="Created within last N days"),
    session: Session = Depends(get_session)
) -> List[TaskPublic]:
    statement = select(TaskDB)

    # Add filters dynamically
    if status:
        statement = statement.where(TaskDB.status == status)

    if title_contains:
        statement = statement.where(TaskDB.title.contains(title_contains))

    if days:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        statement = statement.where(TaskDB.created_at >= cutoff_date)

    tasks = session.exec(statement).all()
    return [TaskPublic.model_validate(task) for task in tasks]
