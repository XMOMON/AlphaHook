from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.database import get_db
from app.models.all import Position, PositionStatus

router = APIRouter()

class PositionResponse(BaseModel):
    id: int
    signal_id: Optional[int] = None
    pair: str
    direction: str
    entry: float
    current_price: Optional[float] = None
    tp1: Optional[float] = None
    tp2: Optional[float] = None
    sl: Optional[float] = None
    size_usd: Optional[float] = None
    pnl_usd: Optional[float] = 0.0
    status: str
    opened_at: Optional[datetime] = None

    class Config:
        from_attributes = True

@router.get("/", response_model=List[PositionResponse])
async def list_positions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Position).where(
            Position.status.in_([PositionStatus.OPEN, PositionStatus.PARTIAL])
        ).order_by(Position.opened_at.desc())
    )
    positions = result.scalars().all()
    return positions
