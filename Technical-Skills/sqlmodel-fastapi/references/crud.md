# CRUD Operations

Complete guide for Create, Read, Update, Delete operations with SQLModel and FastAPI.

## Setup

### Dependencies

```python
from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from typing import List, Optional
from models import TaskDB, TaskCreate, TaskUpdate, TaskPublic
from database import get_session

app = FastAPI()
```

## Create (POST)

### Basic Create

```python
@app.post("/tasks", status_code=status.HTTP_201_CREATED, response_model=TaskPublic)
def create_task(task: TaskCreate, session: Session = Depends(get_session)):
    db_task = TaskDB.model_validate(task)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return TaskPublic.model_validate(db_task)
```

### Create with Validation

```python
@app.post("/tasks", status_code=status.HTTP_201_CREATED, response_model=TaskPublic)
def create_task(task: TaskCreate, session: Session = Depends(get_session)):
    # Check for duplicates
    existing = session.exec(
        select(TaskDB).where(TaskDB.title == task.title)
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Task with this title already exists"
        )

    db_task = TaskDB.model_validate(task)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return TaskPublic.model_validate(db_task)
```

### Create with Relationships

```python
@app.post("/tasks", response_model=TaskPublic)
def create_task(task: TaskCreate, session: Session = Depends(get_session)):
    # Validate related entity exists
    if task.assignee_id:
        assignee = session.get(UserDB, task.assignee_id)
        if not assignee:
            raise HTTPException(status_code=404, detail="Assignee not found")

    db_task = TaskDB.model_validate(task)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return TaskPublic.model_validate(db_task)
```

### Bulk Create

```python
@app.post("/tasks/bulk", response_model=List[TaskPublic])
def create_tasks(tasks: List[TaskCreate], session: Session = Depends(get_session)):
    db_tasks = [TaskDB.model_validate(t) for t in tasks]
    session.add_all(db_tasks)
    session.commit()

    for task in db_tasks:
        session.refresh(task)

    return [TaskPublic.model_validate(t) for t in db_tasks]
```

## Read (GET)

### Read All

```python
@app.get("/tasks", response_model=List[TaskPublic])
def list_tasks(session: Session = Depends(get_session)):
    tasks = session.exec(select(TaskDB)).all()
    return [TaskPublic.model_validate(task) for task in tasks]
```

### Read with Pagination

```python
@app.get("/tasks", response_model=List[TaskPublic])
def list_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session: Session = Depends(get_session)
):
    tasks = session.exec(select(TaskDB).offset(skip).limit(limit)).all()
    return [TaskPublic.model_validate(task) for task in tasks]
```

### Read with Count

```python
@app.get("/tasks")
def list_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session: Session = Depends(get_session)
):
    tasks = session.exec(select(TaskDB).offset(skip).limit(limit)).all()
    total = len(session.exec(select(TaskDB)).all())
    return {
        "items": [TaskPublic.model_validate(t) for t in tasks],
        "total": total,
        "skip": skip,
        "limit": limit
    }
```

### Read One

```python
@app.get("/tasks/{task_id}", response_model=TaskPublic)
def get_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(TaskDB, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskPublic.model_validate(task)
```

### Read with Relationships

```python
from sqlmodel import selectinload

@app.get("/tasks/{task_id}", response_model=TaskPublic)
def get_task(task_id: int, session: Session = Depends(get_session)):
    task = session.exec(
        select(TaskDB)
        .options(selectinload(TaskDB.assignee))
        .where(TaskDB.id == task_id)
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskPublic.model_validate(task)
```

## Update (PUT/PATCH)

### Full Update (PUT)

```python
@app.put("/tasks/{task_id}", response_model=TaskPublic)
def update_task(
    task_id: int,
    task: TaskCreate,  # Full model required
    session: Session = Depends(get_session)
):
    db_task = session.get(TaskDB, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Update all fields
    for key, value in task.model_dump().items():
        setattr(db_task, key, value)

    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return TaskPublic.model_validate(db_task)
```

### Partial Update (PATCH)

```python
@app.patch("/tasks/{task_id}", response_model=TaskPublic)
def update_task(
    task_id: int,
    task_update: TaskUpdate,  # All fields optional
    session: Session = Depends(get_session)
):
    db_task = session.get(TaskDB, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Only update provided fields
    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)

    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return TaskPublic.model_validate(db_task)
```

### Update with Validation

```python
@app.patch("/tasks/{task_id}", response_model=TaskPublic)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    session: Session = Depends(get_session)
):
    db_task = session.get(TaskDB, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Validate status transition
    if task_update.status:
        valid_transitions = {
            "pending": ["in_progress"],
            "in_progress": ["completed", "pending"],
            "completed": []  # Terminal state
        }
        current = db_task.status
        new = task_update.status
        if new not in valid_transitions.get(current, []):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot transition from {current} to {new}"
            )

    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)

    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return TaskPublic.model_validate(db_task)
```

### Optimistic Update

```python
@app.patch("/tasks/{task_id}", response_model=TaskPublic)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    session: Session = Depends(get_session)
):
    db_task = session.get(TaskDB, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Check version for optimistic locking
    if task_update.version is not None and db_task.version != task_update.version:
        raise HTTPException(
            status_code=409,
            detail="Task was modified by another user"
        )

    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)

    db_task.version += 1
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return TaskPublic.model_validate(db_task)
```

## Delete (DELETE)

### Basic Delete

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

### Delete with Confirmation

```python
@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    confirm: bool = Query(False, description="Confirm deletion"),
    session: Session = Depends(get_session)
):
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Set confirm=true to delete"
        )

    task = session.get(TaskDB, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    session.delete(task)
    session.commit()
    return {"message": "Task deleted successfully", "task_id": task_id}
```

### Soft Delete

```python
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(TaskDB, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Mark as deleted instead of removing
    task.is_deleted = True
    task.deleted_at = datetime.now(timezone.utc)

    session.add(task)
    session.commit()
    return {"message": "Task deleted successfully", "task_id": task_id}
```

### Bulk Delete

```python
@app.delete("/tasks")
def delete_tasks(
    task_ids: List[int],
    session: Session = Depends(get_session)
):
    tasks = session.exec(select(TaskDB).where(TaskDB.id.in_(task_ids))).all()

    for task in tasks:
        session.delete(task)

    session.commit()
    return {"message": f"Deleted {len(tasks)} tasks"}
```

## Error Handling Patterns

### 404 Not Found

```python
@app.get("/tasks/{task_id}")
def get_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(TaskDB, task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )
    return TaskPublic.model_validate(task)
```

### 400 Bad Request

```python
@app.post("/tasks")
def create_task(task: TaskCreate, session: Session = Depends(get_session)):
    if task.status == "completed" and not task.completed_at:
        raise HTTPException(
            status_code=400,
            detail="Completed tasks must have completed_at date"
        )
    # ... create task
```

### 409 Conflict

```python
@app.post("/tasks")
def create_task(task: TaskCreate, session: Session = Depends(get_session)):
    existing = session.exec(
        select(TaskDB).where(TaskDB.title == task.title)
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Task with this title already exists"
        )
    # ... create task
```

### 422 Validation Error

```python
from pydantic import ValidationError

try:
    task_validated = TaskCreate(**task_data)
except ValidationError as e:
    raise HTTPException(status_code=422, detail=e.errors())
```

## Best Practices

1. **Use status codes** - 201 for create, 200 for update/delete, 404 for not found
2. **Validate relationships** - Check foreign keys exist
3. **Use exclude_unset** - For partial updates
4. **Return dictionaries** - DELETE should return confirmation, not None
5. **Optimize queries** - Use selectinload for relationships
6. **Handle transactions** - Session commits on success
7. **Use response_model** - Type safety and documentation
8. **Test edge cases** - Non-existent IDs, invalid data
