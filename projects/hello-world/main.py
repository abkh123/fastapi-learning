from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(
    title="Hello World API",
    description="A minimal FastAPI application",
    version="1.0.0"
)

# Simple in-memory storage
items_db = {}
next_id = 1

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

@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    """Delete an item"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    del items_db[item_id]
    return None
