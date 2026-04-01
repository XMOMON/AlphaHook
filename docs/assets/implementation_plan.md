# Pro Paper Trader — Full Feature Sprint (10 Updates)

## Overview
All 10 features implemented across 3 phases: DB migrations → backend logic → frontend UI.

---

## Phase 1 — Backend: DB Migrations & New API Endpoints

### [MODIFY] `models/all.py`
- Add `expires_at: DateTime (nullable)` to **Signal**
- Add `journal: String (nullable)` to **Trade**

### DB Migration (SQLite ALTER TABLE)
- `signals` → add `expires_at`
- `trades` → add `journal`

### [MODIFY] `routers/stats.py`
- Add max drawdown calculation to `GET /api/v1/stats/`
- Add `GET /api/v1/stats/pairs` — per-pair breakdown (pair, trades, wins, win_rate, total_pnl)
- Add `GET /api/v1/stats/history` — returns `balance_history` rows for equity curve chart

### [MODIFY] `routers/signals.py`
- Add `expires_at` to `SignalCreate` schema (optional)

### [MODIFY] `routers/trades.py`
- Add `PATCH /api/v1/trades/{id}/journal` — update journal note on a trade

---

## Phase 2 — Backend: Logic Changes

### [MODIFY] `services/position.py`
- **Signal expiry**: In the pending-signal loop, check if `expires_at` is set and past → auto-cancel with status `CANCELLED`
- **Partial close at TP1**: When TP1 is hit, close 50% of size (create a Trade record for the half-close), reduce `size_usd` by 50%, set status to PARTIAL, move SL to breakeven
- **Signal creation Telegram alert**: Send alert when new signal created (hook into `signals.py` POST)

### [MODIFY] `services/telegram.py`
- Add `send_signal_created_alert(pair, direction, entry, tp1, tp2, sl, confidence)` 
- Add `send_command_bot_loop()` — polls Telegram for incoming `/status`, `/positions`, `/balance` commands and replies with live data

### [MODIFY] `main.py`
- Start `send_command_bot_loop()` as a background asyncio task

---

## Phase 3 — Frontend: New Pages & UI Updates

### [NEW] `frontend/src/Journal.jsx`
- Page showing all closed trades with inline editable journal notes
- Click a trade row → textarea appears → save sends PATCH request

### [MODIFY] `frontend/src/App.jsx`
- Add `/journal` route + nav link

### [MODIFY] `frontend/src/Dashboard.jsx`
- **Equity Curve Chart** (Recharts LineChart) — pulls `/api/v1/stats/history`
- **Portfolio Heatmap** — grid of active positions, colored by PnL % (green→red gradient)
- Replace placeholder stats with live data (total PnL, win rate from stats API)

### [MODIFY] `frontend/src/Signals.jsx`
- Add **R:R ratio** column to signal table (auto-calculated: `(tp2-entry)/(entry-sl)`)
- Add **expires_at** datetime picker to New Signal modal (optional field)

### [MODIFY] `frontend/src/Stats.jsx`
- Add **Max Drawdown** card
- Add **Per-Pair Breakdown** table section

### Install dependency
- `recharts` for the equity curve chart

---

## Verification Plan
1. Run backend, verify all new endpoints work
2. Check signal expiry auto-cancels on page reload
3. Place a test signal, hit TP1 — verify partial close creates a Trade + Telegram fires
4. Open Journal page, add a note, confirm it persists
5. Send `/status` to the bot, confirm it responds
6. Check Dashboard chart renders equity history
7. Check Portfolio Heatmap renders open positions with color coding
