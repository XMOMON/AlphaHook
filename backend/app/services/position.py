import asyncio
from datetime import datetime
from app.database import async_session
from app.models.all import Position, Signal, PositionStatus, DirectionEnum, SignalStatus, Trade, BalanceHistory
from sqlalchemy.future import select
from sqlalchemy.sql import func
from app.services.price import get_current_price
from app.routers.ws import manager
from app.services.telegram import send_entry_alert, send_tp1_alert, send_close_alert, send_signal_expired_alert

STARTING_BALANCE = 10000.0


async def _get_live_balance(db) -> float:
    result = await db.execute(select(func.sum(Trade.pnl_usd)))
    realized = result.scalar() or 0.0
    return STARTING_BALANCE + realized


async def position_monitoring_loop():
    while True:
        try:
            async with async_session() as db:

                # ── 1. Execute pending signals ────────────────────────────────
                result = await db.execute(select(Signal).where(Signal.status == SignalStatus.PENDING))
                signals = result.scalars().all()

                for signal in signals:
                    # Auto-expire stale signals
                    if signal.expires_at and datetime.utcnow() > signal.expires_at:
                        signal.status = SignalStatus.CANCELLED
                        await send_signal_expired_alert(signal.pair, signal.direction.value)
                        continue

                    price = get_current_price(signal.pair)
                    if price <= 0:
                        continue

                    tolerance = 0.005  # 0.5%
                    diff_pct = abs(price - signal.entry) / signal.entry
                    if diff_pct <= tolerance:
                        # 5% dynamic position sizing based on live balance
                        live_balance = await _get_live_balance(db)
                        auto_size = live_balance * 0.05

                        new_pos = Position(
                            signal_id=signal.id,
                            pair=signal.pair,
                            direction=signal.direction,
                            entry=signal.entry,
                            current_price=price,
                            tp1=signal.tp1,
                            tp2=signal.tp2,
                            sl=signal.sl,
                            size_usd=auto_size,
                            status=PositionStatus.OPEN,
                            opened_at=datetime.utcnow()
                        )
                        signal.status = SignalStatus.EXECUTED
                        db.add(new_pos)
                        await db.commit()
                        await manager.broadcast({"type": "position_opened", "data": f"Entered {signal.direction.value} on {signal.pair} at ${price:.4f}"})
                        await send_entry_alert(signal.pair, signal.direction.value, price, auto_size)

                # ── 2. Monitor open positions ─────────────────────────────────
                result = await db.execute(select(Position).where(Position.status.in_([PositionStatus.OPEN, PositionStatus.PARTIAL])))
                positions = result.scalars().all()

                for pos in positions:
                    price = get_current_price(pos.pair)
                    if price <= 0:
                        continue

                    pos.current_price = price

                    # Live PnL
                    if pos.direction == DirectionEnum.LONG:
                        pnl_pct = (price - pos.entry) / pos.entry * 100
                    else:
                        pnl_pct = (pos.entry - price) / pos.entry * 100

                    pos.pnl_usd = pos.size_usd * (pnl_pct / 100)

                    should_close = False
                    exit_reason = ""

                    if pos.direction == DirectionEnum.LONG:
                        if price >= pos.tp2:
                            should_close = True
                            exit_reason = "TP2"
                        elif price >= pos.tp1 and pos.status == PositionStatus.OPEN:
                            # ── Partial close at TP1 (50%) ──
                            half_size = pos.size_usd * 0.5
                            half_pnl_usd = half_size * (pnl_pct / 100)

                            partial_trade = Trade(
                                position_id=pos.id,
                                pair=pos.pair,
                                entry=pos.entry,
                                exit=price,
                                pnl_usd=half_pnl_usd,
                                pnl_pct=pnl_pct,
                                exit_reason="TP1_PARTIAL",
                                opened_at=pos.opened_at,
                                closed_at=datetime.utcnow()
                            )
                            db.add(partial_trade)

                            pos.size_usd = half_size          # reduce to half
                            pos.pnl_usd = pos.size_usd * (pnl_pct / 100)
                            pos.status = PositionStatus.PARTIAL
                            pos.sl = pos.entry                # breakeven SL

                            await send_tp1_alert(pos.pair, pos.direction.value, price, half_pnl_usd)
                            await manager.broadcast({"type": "tp1_hit", "data": f"TP1 hit on {pos.pair} — 50% closed at ${price:.4f}"})

                        elif price <= pos.sl:
                            should_close = True
                            exit_reason = "SL"

                    else:  # SHORT
                        if price <= pos.tp2:
                            should_close = True
                            exit_reason = "TP2"
                        elif price <= pos.tp1 and pos.status == PositionStatus.OPEN:
                            # ── Partial close at TP1 (50%) ──
                            half_size = pos.size_usd * 0.5
                            half_pnl_usd = half_size * (pnl_pct / 100)

                            partial_trade = Trade(
                                position_id=pos.id,
                                pair=pos.pair,
                                entry=pos.entry,
                                exit=price,
                                pnl_usd=half_pnl_usd,
                                pnl_pct=pnl_pct,
                                exit_reason="TP1_PARTIAL",
                                opened_at=pos.opened_at,
                                closed_at=datetime.utcnow()
                            )
                            db.add(partial_trade)

                            pos.size_usd = half_size
                            pos.pnl_usd = pos.size_usd * (pnl_pct / 100)
                            pos.status = PositionStatus.PARTIAL
                            pos.sl = pos.entry               # breakeven SL

                            await send_tp1_alert(pos.pair, pos.direction.value, price, half_pnl_usd)
                            await manager.broadcast({"type": "tp1_hit", "data": f"TP1 hit on {pos.pair} — 50% closed at ${price:.4f}"})

                        elif price >= pos.sl:
                            should_close = True
                            exit_reason = "SL"

                    # ── Full close ────────────────────────────────────────────
                    if should_close:
                        pos.status = PositionStatus.CLOSED
                        pos.exit_price = price
                        pos.exit_reason = exit_reason
                        pos.closed_at = datetime.utcnow()

                        new_trade = Trade(
                            position_id=pos.id,
                            pair=pos.pair,
                            entry=pos.entry,
                            exit=price,
                            pnl_usd=pos.pnl_usd,
                            pnl_pct=pnl_pct,
                            exit_reason=exit_reason,
                            opened_at=pos.opened_at,
                            closed_at=pos.closed_at
                        )
                        db.add(new_trade)
                        await manager.broadcast({"type": "position_closed", "data": f"Closed {pos.pair} ({exit_reason}) PnL: ${pos.pnl_usd:.2f}"})
                        await send_close_alert(pos.pair, pos.direction.value, pos.entry, price, pos.pnl_usd, pnl_pct, exit_reason)

                # ── 3. Snapshot balance history every cycle ───────────────────
                live_balance = await _get_live_balance(db)
                result_unrealized = await db.execute(
                    select(func.sum(Position.pnl_usd)).where(
                        Position.status.in_([PositionStatus.OPEN, PositionStatus.PARTIAL])
                    )
                )
                unrealized = result_unrealized.scalar() or 0.0

                snapshot = BalanceHistory(
                    balance_usd=live_balance,
                    unrealized_pnl=unrealized
                )
                db.add(snapshot)
                await db.commit()

        except Exception as e:
            print(f"Position monitor error: {e}")

        await asyncio.sleep(5)   # snapshot every 5 seconds
