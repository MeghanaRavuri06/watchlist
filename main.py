from datetime import datetime
from typing import List

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import models
import schemas
from database import engine, get_db, Base
from market_data import fetch_quote
from change_detection import evaluate_change

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Market Watchlist")

# Wide open for hackathon dev — tighten before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/watchlist", response_model=schemas.WatchlistItemOut)
def add_item(item: schemas.WatchlistItemCreate, db: Session = Depends(get_db)):
    db_item = models.WatchlistItem(
        symbol=item.symbol.upper(),
        display_name=item.display_name,
        reason=item.reason,
        target_price=item.target_price,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@app.delete("/watchlist/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.WatchlistItem).filter(models.WatchlistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    db.delete(item)
    db.commit()
    return {"ok": True}


@app.get("/watchlist", response_model=List[schemas.WatchlistItemWithQuote])
def get_watchlist(db: Session = Depends(get_db)):
    """
    Current state of the watchlist. Also writes a PriceSnapshot for every
    item on every call — that's what gives the /watchlist/diff endpoint real
    history to compare against later, instead of needing a background job
    running 24/7 (fine for a hackathon; swap for a scheduled job to scale).
    """
    items = db.query(models.WatchlistItem).all()
    results: List[schemas.WatchlistItemWithQuote] = []

    for item in items:
        quote = fetch_quote(item.symbol)

        if quote is None:
            results.append(schemas.WatchlistItemWithQuote(
                id=item.id,
                symbol=item.symbol,
                display_name=item.display_name,
                reason=item.reason,
                target_price=item.target_price,
                price=None,
                pct_change=None,
                is_meaningful=False,
                flags=["data_unavailable"],
                captured_at=datetime.utcnow(),
            ))
            continue

        evald = evaluate_change(quote, item.target_price)

        snap = models.PriceSnapshot(
            symbol=item.symbol,
            price=quote["price"],
            volume=quote.get("volume"),
            pct_change_day=evald["pct_change"],
            is_meaningful=int(evald["is_meaningful"]),
            reason_flag=",".join(evald["flags"]) if evald["flags"] else None,
        )
        db.add(snap)

        results.append(schemas.WatchlistItemWithQuote(
            id=item.id,
            symbol=item.symbol,
            display_name=item.display_name,
            reason=item.reason,
            target_price=item.target_price,
            price=quote["price"],
            pct_change=evald["pct_change"],
            is_meaningful=evald["is_meaningful"],
            flags=evald["flags"],
            z_score=evald.get("z_score"),
            volume_ratio=evald.get("volume_ratio"),
            captured_at=snap.captured_at,
        ))

    db.commit()
    return results


@app.get("/watchlist/diff", response_model=schemas.DiffResponse)
def get_diff(db: Session = Depends(get_db)):
    """
    The 'since you last checked' comparison view.

    Anchor point = the most recent PriceSnapshot taken before the last
    logged visit. Compared against the most recent snapshot overall (= now).
    Calling this endpoint also logs a new visit, so the NEXT diff starts
    from this moment.
    """
    last_visit = (
        db.query(models.VisitLog)
        .order_by(models.VisitLog.visited_at.desc())
        .first()
    )
    last_visit_time = last_visit.visited_at if last_visit else None

    items = db.query(models.WatchlistItem).all()
    comparisons: List[schemas.ItemComparison] = []

    for item in items:
        snap_query = db.query(models.PriceSnapshot).filter(
            models.PriceSnapshot.symbol == item.symbol
        )

        if last_visit_time:
            then_snap = (
                snap_query.filter(models.PriceSnapshot.captured_at <= last_visit_time)
                .order_by(models.PriceSnapshot.captured_at.desc())
                .first()
            )
        else:
            # First-ever visit: compare against the earliest snapshot we have.
            then_snap = snap_query.order_by(models.PriceSnapshot.captured_at.asc()).first()

        now_snap = (
            db.query(models.PriceSnapshot)
            .filter(models.PriceSnapshot.symbol == item.symbol)
            .order_by(models.PriceSnapshot.captured_at.desc())
            .first()
        )

        if not then_snap or not now_snap:
            continue  # no history yet for this symbol — nothing to compare

        price_then = then_snap.price
        price_now = now_snap.price
        delta_pct = round(((price_now - price_then) / price_then) * 100, 2) if price_then else 0.0

        target_hit = False
        if item.target_price is not None:
            target_hit = (
                (price_then < item.target_price <= price_now)
                or (price_then > item.target_price >= price_now)
            )

        comparisons.append(schemas.ItemComparison(
            symbol=item.symbol,
            display_name=item.display_name,
            reason=item.reason,
            price_then=price_then,
            price_now=price_now,
            delta_pct=delta_pct,
            is_meaningful=bool(now_snap.is_meaningful),
            flags=now_snap.reason_flag.split(",") if now_snap.reason_flag else [],
            target_hit=target_hit,
        ))

    db.add(models.VisitLog(visited_at=datetime.utcnow()))
    db.commit()

    return schemas.DiffResponse(last_visit_at=last_visit_time, comparisons=comparisons)
