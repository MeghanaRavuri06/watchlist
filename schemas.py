from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class WatchlistItemCreate(BaseModel):
    symbol: str
    display_name: Optional[str] = None
    reason: Optional[str] = None
    target_price: Optional[float] = None


class WatchlistItemOut(BaseModel):
    id: int
    symbol: str
    display_name: Optional[str] = None
    reason: Optional[str] = None
    target_price: Optional[float] = None

    class Config:
        from_attributes = True


class WatchlistItemWithQuote(BaseModel):
    id: int
    symbol: str
    display_name: Optional[str] = None
    reason: Optional[str] = None
    target_price: Optional[float] = None
    price: Optional[float] = None
    pct_change: Optional[float] = None
    is_meaningful: bool = False
    flags: List[str] = []
    z_score: Optional[float] = None
    volume_ratio: Optional[float] = None
    captured_at: Optional[datetime] = None


class ItemComparison(BaseModel):
    symbol: str
    display_name: Optional[str] = None
    reason: Optional[str] = None
    price_then: float
    price_now: float
    delta_pct: float
    is_meaningful: bool
    flags: List[str] = []
    target_hit: bool = False


class DiffResponse(BaseModel):
    last_visit_at: Optional[datetime] = None
    comparisons: List[ItemComparison]
