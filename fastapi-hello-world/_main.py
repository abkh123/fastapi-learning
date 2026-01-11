from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI(
    title="Hello World API",
    description="A minimal FastAPI application",
    version="1.0.0"
)

# Simple in-memory storage
items_db = {}
next_id = 1

# Task storage
tasks_db = {}
next_task_id = 1

# Pydantic model
class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float

class ItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float

# Task models
class TaskCreate(BaseModel):
    title: str
    description: str | None = None

class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None= None
    status: str | None = None

class Task(BaseModel):
    title: str = Field(..., min_length=1)  # ✓ Reject empty strings
    description: Optional[str] = None
    status: str = "pending"  # pending, in_progress, completed
    priority: int = 3  # 1-5 scale

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    priority: int

class SearchResult(BaseModel):
    id: int
    title: str
    item_type: str  # "item" or "task"

@app.get("/")
def read_root():
    """Root endpoint - welcome message"""
    return {
        "message": "Hello World",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy"}

@app.get("/items", response_model=list[ItemResponse])
def list_items():
    """Get all items"""
    return [{"id": item_id, **item} for item_id, item in items_db.items()]

@app.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int):
    """Get a specific item by ID"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"id": item_id, **items_db[item_id]}

@app.post("/items", response_model=ItemResponse, status_code=201)
def create_item(item: Item):
    """Create a new item"""
    global next_id
    item_id = next_id
    items_db[item_id] = item.model_dump()
    next_id += 1
    return {"id": item_id, **items_db[item_id]}

@app.put("/items/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item: Item):
    """Update an existing item"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    items_db[item_id] = item.model_dump()
    return {"id": item_id, **items_db[item_id]}

@app.delete("/items/{item_id}", status_code=200)
def delete_item(item_id: int) -> dict:
    """Delete an item"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    del items_db[item_id]
    return {"message": "Item deleted successfully", "id": item_id}

# Task endpoints
@app.get("/tasks", response_model=list[TaskResponse])
def list_tasks() -> list[dict]:
    """Get all tasks"""
    return [{"id": task_id, **task} for task_id, task in tasks_db.items()]

@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int) -> dict:
    """Get a specific task by ID (demonstrates path parameters)"""
    if task_id not in tasks_db:
        raise HTTPException(
            status_code=404,
            detail=f"Task with id {task_id} not found"
        )
    return {"id": task_id, **tasks_db[task_id]}

@app.post("/tasks", response_model=TaskResponse, status_code=201)
def create_task(task: Task) -> dict:
    """Create a new task"""
    global next_task_id
    task_id = next_task_id
    tasks_db[task_id] = task.model_dump()
    next_task_id += 1
    return {"id": task_id, **tasks_db[task_id]}

# Search endpoint
@app.get("/search", response_model=list[SearchResult])
def search_items_and_tasks(
    query: str = Query(..., min_length=1, max_length=100, description="Search text"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum item price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum item price"),
    status: Optional[str] = Query(None, description="Task status filter")
) -> list[dict]:
    """
    Search across tasks and items with query parameters.

    - **query**: Required search text (1-100 chars)
    - **min_price**: Optional minimum price filter for items
    - **max_price**: Optional maximum price filter for items
    - **status**: Optional status filter for tasks
    """
    results = []

    # Search items by name/description with price filters
    for item_id, item_data in items_db.items():
        name = item_data.get("name", "")
        desc = item_data.get("description", "")

        if query.lower() in name.lower() or query.lower() in desc.lower():
            price = item_data.get("price", 0)

            # Apply price filters
            if min_price is not None and price < min_price:
                continue
            if max_price is not None and price > max_price:
                continue

            results.append({
                "id": item_id,
                "title": name,
                "item_type": "item"
            })

    # Search tasks by title with status filter
    for task_id, task_data in tasks_db.items():
        title = task_data.get("title", "")

        if query.lower() in title.lower():
            # Apply status filter
            if status and task_data.get("status") != status:
                continue

            results.append({
                "id": task_id,
                "title": title,
                "item_type": "task"
            })

    return results
