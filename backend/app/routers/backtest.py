from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from datetime import datetime
from app.database import get_db
from app.services.backtest import run_backtest

router = APIRouter(prefix="/backtest", tags=["backtest"])


class BacktestRequest(BaseModel):
    pair: str = Field(..., example="BTC/USDT")
    start_date: datetime = Field(..., example="2024-01-01T00:00:00Z")
    end_date: datetime = Field(..., example="2024-12-31T23:59:59Z")
    initial_balance: float = Field(10000.0, ge=100)
    risk_per_trade: float = Field(0.02, ge=0.001, le=0.1)
    slippage_pct: float = Field(0.001, ge=0, le=0.05)
    commission_pct: float = Field(0.001, ge=0, le=0.05)


@router.post("/")
async def run_backtest_endpoint(
    request: BacktestRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await run_backtest(
            db=db,
            pair=request.pair,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_balance=request.initial_balance,
            risk_per_trade=request.risk_per_trade,
            slippage_pct=request.slippage_pct,
            commission_pct=request.commission_pct
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
