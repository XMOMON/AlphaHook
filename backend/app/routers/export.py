import csv
import io
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.all import Trade

router = APIRouter()


@router.get("/trades", summary="Export all closed trades as CSV")
async def export_trades_csv(db: AsyncSession = Depends(get_db)):
    """Download all completed trades as a CSV file suitable for Excel/Numbers."""
    result = await db.execute(select(Trade).order_by(Trade.closed_at.desc()))
    trades = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        "Trade ID",
        "Pair",
        "Entry Price",
        "Exit Price",
        "PnL (USD)",
        "PnL (%)",
        "Exit Reason",
        "Opened At",
        "Closed At",
        "Duration (min)",
    ])

    # Data rows
    for t in trades:
        opened = t.opened_at or datetime.now(timezone.utc)
        closed = t.closed_at or datetime.now(timezone.utc)

        # Calculate duration in minutes
        if t.opened_at and t.closed_at:
            duration_min = round((t.closed_at - t.opened_at).total_seconds() / 60, 1)
        else:
            duration_min = ""

        writer.writerow([
            t.id,
            t.pair,
            round(t.entry, 6),
            round(t.exit, 6),
            round(t.pnl_usd, 2),
            round(t.pnl_pct, 4),
            t.exit_reason,
            t.opened_at.strftime("%Y-%m-%d %H:%M:%S") if t.opened_at else "",
            t.closed_at.strftime("%Y-%m-%d %H:%M:%S") if t.closed_at else "",
            duration_min,
        ])

    output.seek(0)
    filename = f"paper_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
