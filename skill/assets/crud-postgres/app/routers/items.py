from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import Item
from app.schemas import ItemCreate, ItemUpdate, ItemResponse
from app.dependencies import get_item_or_404

router = APIRouter(prefix="/items", tags=["items"])

@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    item: ItemCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new item"""
    db_item = Item(**item.model_dump())
    db.add(db_item)
    await db.flush()
    await db.refresh(db_item)
    return db_item

@router.get("/", response_model=list[ItemResponse])
async def list_items(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of items to return"),
    db: AsyncSession = Depends(get_db)
):
    """List all items with pagination"""
    result = await db.execute(
        select(Item).offset(skip).limit(limit)
    )
    items = result.scalars().all()
    return items

@router.get("/count")
async def count_items(db: AsyncSession = Depends(get_db)):
    """Get total count of items"""
    result = await db.execute(select(func.count(Item.id)))
    count = result.scalar()
    return {"count": count}

@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(item: Item = Depends(get_item_or_404)):
    """Get a specific item by ID"""
    return item

@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    item_update: ItemUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an item"""
    result = await db.execute(select(Item).where(Item.id == item_id))
    db_item = result.scalar_one_or_none()

    if not db_item:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Item not found")

    # Update only provided fields
    update_data = item_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)

    await db.flush()
    await db.refresh(db_item)
    return db_item

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item: Item = Depends(get_item_or_404),
    db: AsyncSession = Depends(get_db)
):
    """Delete an item"""
    await db.delete(item)
    return None
