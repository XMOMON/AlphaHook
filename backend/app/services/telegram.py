import aiohttp
import asyncio
import os
from datetime import datetime

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ─────────────────────────────────────────────
# Core sender
# ─────────────────────────────────────────────
async def send_telegram(message: str, chat_id: str = None):
    """Send a message via Telegram Bot API. Silently fails if not configured."""
    token = TELEGRAM_BOT_TOKEN
    cid = chat_id or TELEGRAM_CHAT_ID
    if not token or not cid:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": cid,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status != 200:
                    print(f"Telegram API error: {resp.status}")
    except Exception as e:
        print(f"Telegram send error: {e}")


# ─────────────────────────────────────────────
# Trade alerts
# ─────────────────────────────────────────────
async def send_signal_created_alert(pair: str, direction: str, entry: float, tp1: float, tp2: float, sl: float, confidence: str, expires_at=None):
    arrow = "🟢" if direction == "LONG" else "🔴"
    rr = round((tp2 - entry) / (entry - sl), 2) if direction == "LONG" and (entry - sl) != 0 else \
         round((entry - tp2) / (sl - entry), 2) if direction == "SHORT" and (sl - entry) != 0 else 0.0
    expiry_line = f"\nExpires: <b>{expires_at.strftime('%Y-%m-%d %H:%M')}</b>" if expires_at else ""
    msg = (
        f"{arrow} <b>NEW SIGNAL</b>\n\n"
        f"Pair: <b>{pair}</b>\n"
        f"Direction: <b>{direction}</b>\n"
        f"Entry: <b>${entry:,.4f}</b>\n"
        f"TP1: <b>${tp1:,.4f}</b>  TP2: <b>${tp2:,.4f}</b>\n"
        f"SL: <b>${sl:,.4f}</b>\n"
        f"R:R: <b>{rr}R</b>  |  Confidence: <b>{confidence.replace('_', ' ')}</b>"
        f"{expiry_line}\n\n"
        f"⏳ Waiting for entry trigger..."
    )
    await send_telegram(msg)


async def send_entry_alert(pair: str, direction: str, entry_price: float, size_usd: float):
    arrow = "🟢" if direction == "LONG" else "🔴"
    msg = (
        f"{arrow} <b>ENTRY TRIGGERED</b>\n\n"
        f"Pair: <b>{pair}</b>\n"
        f"Direction: <b>{direction}</b>\n"
        f"Entry: <b>${entry_price:,.4f}</b>\n"
        f"Size: <b>${size_usd:,.2f}</b>\n\n"
        f"⏳ Monitoring TP/SL..."
    )
    await send_telegram(msg)


async def send_tp1_alert(pair: str, direction: str, price: float, partial_pnl: float = 0.0):
    pnl_line = f"\n💰 Partial PnL: <b>+${partial_pnl:,.2f}</b>" if partial_pnl > 0 else ""
    msg = (
        f"🎯 <b>TP1 HIT</b>\n\n"
        f"Pair: <b>{pair}</b>\n"
        f"Direction: <b>{direction}</b>\n"
        f"Price: <b>${price:,.4f}</b>"
        f"{pnl_line}\n\n"
        f"🔒 50% closed · SL moved to breakeven"
    )
    await send_telegram(msg)


async def send_close_alert(pair: str, direction: str, entry: float, exit_price: float, pnl_usd: float, pnl_pct: float, reason: str):
    icon = "✅" if pnl_usd >= 0 else "❌"
    pnl_sign = "+" if pnl_usd >= 0 else ""
    msg = (
        f"{icon} <b>POSITION CLOSED</b>\n\n"
        f"Pair: <b>{pair}</b>\n"
        f"Direction: <b>{direction}</b>\n"
        f"Entry: ${entry:,.4f}\n"
        f"Exit: ${exit_price:,.4f}\n"
        f"Reason: <b>{reason}</b>\n\n"
        f"PnL: <b>{pnl_sign}${pnl_usd:,.2f} ({pnl_sign}{pnl_pct:.2f}%)</b>"
    )
    await send_telegram(msg)


async def send_signal_expired_alert(pair: str, direction: str):
    msg = (
        f"⌛ <b>SIGNAL EXPIRED</b>\n\n"
        f"Pair: <b>{pair}</b>  |  Direction: <b>{direction}</b>\n"
        f"Signal auto-cancelled — price never reached entry."
    )
    await send_telegram(msg)


# ─────────────────────────────────────────────
# Command Bot (two-way: /status, /positions, /balance)
# ─────────────────────────────────────────────
_last_update_id = 0


async def _get_updates():
    global _last_update_id
    token = TELEGRAM_BOT_TOKEN
    if not token:
        return []
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    params = {"timeout": 5, "offset": _last_update_id + 1}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                if data.get("ok"):
                    updates = data.get("result", [])
                    if updates:
                        _last_update_id = updates[-1]["update_id"]
                    return updates
    except Exception as e:
        print(f"Telegram getUpdates error: {e}")
    return []


async def _handle_command(text: str, chat_id: str):
    """Handle incoming bot commands by fetching live data."""
    from app.database import async_session
    from app.models.all import Position, Trade, PositionStatus
    from sqlalchemy.future import select
    from sqlalchemy.sql import func

    text = text.strip().lower().split()[0]  # grab first word

    if text == "/status" or text == "/start":
        async with async_session() as db:
            r1 = await db.execute(select(func.count(Position.id)).where(Position.status.in_([PositionStatus.OPEN, PositionStatus.PARTIAL])))
            open_count = r1.scalar() or 0
            r2 = await db.execute(select(func.sum(Trade.pnl_usd)))
            realized = r2.scalar() or 0.0
            r3 = await db.execute(select(func.sum(Position.pnl_usd)).where(Position.status.in_([PositionStatus.OPEN, PositionStatus.PARTIAL])))
            unrealized = r3.scalar() or 0.0
            balance = 10000.0 + realized
            equity = balance + unrealized
        sign = "+" if realized >= 0 else ""
        msg = (
            f"📊 <b>Pro Paper Trader — Status</b>\n\n"
            f"💰 Equity: <b>${equity:,.2f}</b>\n"
            f"📈 Balance: <b>${balance:,.2f}</b>\n"
            f"Realized PnL: <b>{sign}${realized:,.2f}</b>\n"
            f"Unrealized PnL: <b>${unrealized:,.2f}</b>\n"
            f"Open Positions: <b>{open_count}</b>"
        )
        await send_telegram(msg, chat_id)

    elif text == "/positions":
        async with async_session() as db:
            r = await db.execute(select(Position).where(Position.status.in_([PositionStatus.OPEN, PositionStatus.PARTIAL])))
            positions = r.scalars().all()

        if not positions:
            await send_telegram("📭 No open positions right now.", chat_id)
            return

        lines = ["📋 <b>Open Positions</b>\n"]
        for p in positions:
            sign = "+" if p.pnl_usd >= 0 else ""
            icon = "🟢" if p.direction.value == "LONG" else "🔴"
            lines.append(
                f"{icon} <b>{p.pair}</b> {p.direction.value}\n"
                f"   Entry: ${p.entry:,.4f}  →  Now: ${p.current_price:,.4f}\n"
                f"   PnL: <b>{sign}${p.pnl_usd:,.2f}</b>  |  Size: ${p.size_usd:,.0f}\n"
            )
        await send_telegram("\n".join(lines), chat_id)

    elif text == "/balance":
        async with async_session() as db:
            r = await db.execute(select(func.sum(Trade.pnl_usd)))
            realized = r.scalar() or 0.0
            r2 = await db.execute(select(func.sum(Position.pnl_usd)).where(Position.status.in_([PositionStatus.OPEN, PositionStatus.PARTIAL])))
            unrealized = r2.scalar() or 0.0
        balance = 10000.0 + realized
        equity = balance + unrealized
        sign = "+" if realized >= 0 else ""
        msg = (
            f"💰 <b>Account Balance</b>\n\n"
            f"Equity: <b>${equity:,.2f}</b>\n"
            f"Realized PnL: <b>{sign}${realized:,.2f}</b>\n"
            f"Unrealized: <b>${unrealized:,.2f}</b>"
        )
        await send_telegram(msg, chat_id)

    elif text == "/help":
        await send_telegram(
            "🤖 <b>Pro Paper Trader Bot</b>\n\n"
            "/status — Account overview\n"
            "/positions — All open positions\n"
            "/balance — Quick balance check\n"
            "/help — This message",
            chat_id
        )


async def command_bot_loop():
    """Background polling loop for Telegram commands."""
    if not TELEGRAM_BOT_TOKEN:
        return
    print("Telegram command bot started — listening for /status /positions /balance")
    while True:
        try:
            updates = await _get_updates()
            for update in updates:
                msg = update.get("message", {})
                text = msg.get("text", "")
                chat_id = str(msg.get("chat", {}).get("id", ""))
                if text.startswith("/") and chat_id:
                    await _handle_command(text, chat_id)
        except Exception as e:
            print(f"Command bot error: {e}")
        await asyncio.sleep(2)
