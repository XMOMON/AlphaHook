from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.all import Trade

router = APIRouter()


class JournalUpdate(BaseModel):
    journal: Optional[str] = ""


@router.get("/")
async def list_trades(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Trade).order_by(Trade.closed_at.desc()))
    trades = result.scalars().all()
    return [
        {
            "id": t.id,
            "pair": t.pair,
            "entry": t.entry,
            "exit": t.exit,
            "pnl_usd": t.pnl_usd,
            "pnl_pct": t.pnl_pct,
            "exit_reason": t.exit_reason,
            "journal": t.journal or "",
            "opened_at": t.opened_at.isoformat() if t.opened_at else None,
            "closed_at": t.closed_at.isoformat() if t.closed_at else None,
        }
        for t in trades
    ]


@router.patch("/{trade_id}/journal")
async def update_journal(trade_id: int, body: JournalUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Trade).where(Trade.id == trade_id))
    trade = result.scalar_one_or_none()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    trade.journal = body.journal
    await db.commit()
    return {"status": "ok", "id": trade_id}
