from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
from app.database import get_db
from app.models.all import Trade, Position, PositionStatus, BalanceHistory

router = APIRouter()

STARTING_BALANCE = 10000.0


def _calc_max_drawdown(balance_rows: list) -> float:
    """Calculate max peak-to-trough drawdown % from balance history."""
    if not balance_rows:
        return 0.0
    peak = STARTING_BALANCE
    max_dd = 0.0
    for row in balance_rows:
        val = row.balance_usd
        if val > peak:
            peak = val
        dd = (peak - val) / peak * 100 if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    return round(max_dd, 2)


@router.get("/")
async def get_stats(db: AsyncSession = Depends(get_db)):
    # Realized PnL
    result_trades = await db.execute(select(func.sum(Trade.pnl_usd)))
    realized_pnl = result_trades.scalar() or 0.0

    # Unrealized PnL
    result_pos = await db.execute(
        select(func.sum(Position.pnl_usd)).where(
            Position.status.in_([PositionStatus.OPEN, PositionStatus.PARTIAL])
        )
    )
    unrealized_pnl = result_pos.scalar() or 0.0

    balance = STARTING_BALANCE + realized_pnl
    equity = balance + unrealized_pnl

    # Trade counts
    result_total = await db.execute(select(func.count(Trade.id)))
    total_trades = result_total.scalar() or 0

    result_wins = await db.execute(select(func.count(Trade.id)).where(Trade.pnl_usd > 0))
    wins = result_wins.scalar() or 0

    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0

    result_avg = await db.execute(select(func.avg(Trade.pnl_pct)))
    avg_pnl_pct = result_avg.scalar() or 0.0

    result_best = await db.execute(select(func.max(Trade.pnl_usd)))
    best_trade = result_best.scalar() or 0.0

    result_worst = await db.execute(select(func.min(Trade.pnl_usd)))
    worst_trade = result_worst.scalar() or 0.0

    # Max drawdown from balance history
    result_hist = await db.execute(select(BalanceHistory).order_by(BalanceHistory.timestamp))
    history_rows = result_hist.scalars().all()
    max_drawdown = _calc_max_drawdown(history_rows)

    return {
        "starting_balance": STARTING_BALANCE,
        "balance": balance,
        "equity": equity,
        "realized_pnl": realized_pnl,
        "unrealized_pnl": unrealized_pnl,
        "total_trades": total_trades,
        "wins": wins,
        "win_rate": win_rate,
        "avg_pnl_pct": avg_pnl_pct,
        "best_trade": best_trade,
        "worst_trade": worst_trade,
        "max_drawdown": max_drawdown,
    }


@router.get("/balance")
async def get_balance(db: AsyncSession = Depends(get_db)):
    result_trades = await db.execute(select(func.sum(Trade.pnl_usd)))
    realized_pnl = result_trades.scalar() or 0.0

    result_pos = await db.execute(
        select(func.sum(Position.pnl_usd)).where(
            Position.status.in_([PositionStatus.OPEN, PositionStatus.PARTIAL])
        )
    )
    unrealized_pnl = result_pos.scalar() or 0.0

    balance = STARTING_BALANCE + realized_pnl
    equity = balance + unrealized_pnl

    return {
        "starting_balance": STARTING_BALANCE,
        "balance": balance,
        "equity": equity,
        "realized_pnl": realized_pnl,
        "unrealized_pnl": unrealized_pnl,
    }


@router.get("/history")
async def get_balance_history(db: AsyncSession = Depends(get_db)):
    """Returns timestamped balance snapshots for the equity curve chart."""
    result = await db.execute(
        select(BalanceHistory).order_by(BalanceHistory.timestamp).limit(500)
    )
    rows = result.scalars().all()
    return [
        {
            "timestamp": r.timestamp.isoformat(),
            "balance": round(r.balance_usd, 2),
            "unrealized_pnl": round(r.unrealized_pnl, 2),
            "equity": round(r.balance_usd + r.unrealized_pnl, 2),
        }
        for r in rows
    ]


@router.get("/pairs")
async def get_pair_stats(db: AsyncSession = Depends(get_db)):
    """Per-pair performance breakdown."""
    result = await db.execute(select(Trade))
    trades = result.scalars().all()

    pairs: dict = {}
    for t in trades:
        p = t.pair
        if p not in pairs:
            pairs[p] = {"pair": p, "trades": 0, "wins": 0, "total_pnl": 0.0, "total_pnl_pct": 0.0}
        pairs[p]["trades"] += 1
        pairs[p]["total_pnl"] += t.pnl_usd
        pairs[p]["total_pnl_pct"] += t.pnl_pct
        if t.pnl_usd > 0:
            pairs[p]["wins"] += 1

    result_list = []
    for p, d in pairs.items():
        d["win_rate"] = round(d["wins"] / d["trades"] * 100, 1) if d["trades"] > 0 else 0.0
        d["avg_pnl_pct"] = round(d["total_pnl_pct"] / d["trades"], 2) if d["trades"] > 0 else 0.0
        d["total_pnl"] = round(d["total_pnl"], 2)
        result_list.append(d)

    return sorted(result_list, key=lambda x: x["total_pnl"], reverse=True)
