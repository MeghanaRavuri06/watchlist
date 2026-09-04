from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, Text

from database import Base


class WatchlistItem(Base):
    """A stock the user is tracking, plus WHY they're tracking it."""

    __tablename__ = "watchlist_items"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)         # e.g. "RELIANCE.NS"
    display_name = Column(String, nullable=True)
    reason = Column(Text, nullable=True)                        # free text: why they added it
    target_price = Column(Float, nullable=True)                 # optional level they're watching for
    added_at = Column(DateTime, default=datetime.utcnow)


class PriceSnapshot(Base):
    """A point-in-time record of a symbol's price + computed signals.

    We store one of these every time /watchlist is fetched, so the diff
    endpoint always has a real historical point to compare "then" vs "now" —
    instead of trying to reconstruct history from a live API call.
    """

    __tablename__ = "price_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    price = Column(Float, nullable=False)
    volume = Column(Integer, nullable=True)
    captured_at = Column(DateTime, default=datetime.utcnow, index=True)
    pct_change_day = Column(Float, nullable=True)
    is_meaningful = Column(Integer, default=0)   # 0/1
    reason_flag = Column(String, nullable=True)  # comma-joined: "volatility,volume_spike"


class VisitLog(Base):
    """Every time the diff endpoint is hit, we log it as a 'visit'.

    The most recent visit before now = "the last time the user checked" —
    that's the anchor point for the before/after comparison view.
    """

    __tablename__ = "visit_log"

    id = Column(Integer, primary_key=True, index=True)
    visited_at = Column(DateTime, default=datetime.utcnow)
