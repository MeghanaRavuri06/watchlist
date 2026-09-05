# Watchlist, But It Remembers Why You Added Every Stock

Built for Groww Code 2026.

## The idea

Most watchlists track a symbol. This one tracks *why you're watching it* —
and uses that context to decide what actually deserves your attention when
you come back.

Three requirements were given, and each has a deliberate answer beyond the
obvious version:

| Requirement | The obvious version | What this does instead |
|---|---|---|
| Create/manage a watchlist | Add a symbol, see a list | Capture *why* you added it — a thesis, an earnings date, a price target — so that context can be used later |
| View latest market info | Price + % change | Price + % change, plus a plain-English status line, a freshness timestamp, and an expandable view of the actual volatility/volume numbers behind any flag |
| See what's changed since last visit | A list of price moves | A direct before/after comparison against your last visit, with the reasoning behind every flag shown, not hidden behind a generic badge |

## What counts as "meaningful"

A stock is flagged only if at least one of these is true:

1. **Volatility check** — today's move is ≥ 2 standard deviations from that
   stock's own recent daily volatility (a z-score, not a flat % rule — a 3%
   move means something different for a stable large-cap than for a
   volatile small-cap).
2. **Volume check** — today's volume is ≥ 3x the 30-day average, meaning
   the move is backed by real trading activity, not noise on thin volume.
3. **Target check** — the price crossed the exact level the user specified
   when they added the stock.

Each check is kept separate (not blended into one score) so the UI can show
*which* reason triggered the flag, with the actual numbers, rather than
just a label.


# Catchup — Your smart market watchlist that keeps you ahead of every market move

Built for Groww Code 2026.

## The idea

Most watchlists track a symbol. This one tracks *why you're watching it* —
and uses that context to decide what actually deserves your attention when
you come back.

Three requirements were given, and each has a deliberate answer beyond the
obvious version:

| Requirement | The obvious version | What this does instead |
|---|---|---|
| Create/manage a watchlist | Add a symbol, see a list | Capture *why* you added it — a thesis, an earnings date, a price target — so that context can be used later |
| View latest market info | Price + % change | Price + % change, plus a plain-English status line, a freshness timestamp, and an expandable view of the actual volatility/volume numbers behind any flag |
| See what's changed since last visit | A list of price moves | A direct before/after comparison against your last visit, with the reasoning behind every flag shown, not hidden behind a generic badge |

## What counts as "meaningful"

A stock is flagged only if at least one of these is true:

1. **Volatility check** — today's move is ≥ 2 standard deviations from that
   stock's own recent daily volatility (a z-score, not a flat % rule — a 3%
   move means something different for a stable large-cap than for a
   volatile small-cap).
2. **Volume check** — today's volume is ≥ 3x the 30-day average, meaning
   the move is backed by real trading activity, not noise on thin volume.
3. **Target check** — the price crossed the exact level the user specified
   when they added the stock.

Each check is kept separate (not blended into one score) so the UI can show
*which* reason triggered the flag, with the actual numbers, rather than
just a label.

## Architecture
backend/ FastAPI + SQLite
main.py - API endpoints (watchlist CRUD, diff)
models.py - DB schema: watchlist items, price snapshots, visit log
schemas.py - request/response types
market_data.py - Yahoo Finance wrapper (yfinance)
change_detection.py - the "meaningful change" logic
test_flow.py - end-to-end test with mocked price data

frontend/ React + Vite
src/App.jsx - Watchlist view + "Since you last checked" diff view
src/api.js - backend API client
src/index.css - styling

**How the diff works:** every time `/watchlist` is called, a price snapshot
is stored. `/watchlist/diff` compares the most recent snapshot before your
last logged visit ("then") against the latest snapshot ("now"), so the
comparison is a real historical record, not a live recomputation.

## Live demo

- Frontend: https://watchlist-ochre-xi.vercel.app/
- Backend API: https://watchlist-m7j5.onrender.com/
- Swagger docs: https://watchlist-m7j5.onrender.com/docs

## Running locally

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend** (separate terminal):
```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (usually `http://localhost:5173`). Add a stock
using an NSE ticker with the `.NS` suffix (e.g. `RELIANCE.NS`,
`HDFCBANK.NS`, `TATAMOTORS.NS`), with a reason and optional target price.

## Scope and known limitations

Built and tested within a 72-hour window — these are deliberate scope cuts,
not oversights:

- **Single-user, no auth.** The schema has room for a `user_id` column;
  adding real multi-user auth would be the first extension.
- **No fallback data source yet.** If Yahoo Finance is unreachable or
  rate-limits, the affected stock shows `data_unavailable` rather than
  silently showing stale data — correct behavior, but a second data source
  would make this more resilient.
- **Thresholds are fixed constants** (2 std devs, 3x volume) rather than
  configurable per stock or per user — a reasonable v1 default, tunable
  later based on real usage.

## Tested edge cases

- Invalid/nonexistent stock symbol → shows `data_unavailable`, doesn't crash
- Backend unreachable → frontend shows a clear connection error, not a blank
  page
- Empty watchlist → clear empty state
- First-ever visit (no prior snapshot) → diff view handles gracefully
