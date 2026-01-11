from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Item
from fastapi import Depends, HTTPException, status

async def get_item_or_404(
    item_id: int,
    db: AsyncSession = Depends(get_db)
) -> Item:
    """
    Dependency to get an item by ID or raise 404 if not found.
    """
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )

    return item
