

from typing import Optional


VOLATILITY_Z_THRESHOLD = 2.0     # move is >= 2 std devs from this stock's norm
VOLUME_SPIKE_RATIO = 3.0         # today's volume is >= 3x the 30-day average


def evaluate_change(quote: dict, target_price: Optional[float]) -> dict:
    price = quote["price"]
    prev_close = quote["prev_close"]

    pct_change = ((price - prev_close) / prev_close) if prev_close else 0.0

    stdev = quote.get("daily_return_stdev_30d") or 0.0
    z_score = (pct_change / stdev) if stdev > 0 else 0.0

    volume = quote.get("volume") or 0
    avg_volume = quote.get("avg_volume_30d") or 0
    volume_ratio = (volume / avg_volume) if avg_volume > 0 else 0.0

    flags = []
    if abs(z_score) >= VOLATILITY_Z_THRESHOLD:
        flags.append("volatility")
    if volume_ratio >= VOLUME_SPIKE_RATIO:
        flags.append("volume_spike")
    if target_price is not None:
        crossed = (prev_close < target_price <= price) or (prev_close > target_price >= price)
        if crossed:
            flags.append("target_hit")

    return {
        "pct_change": round(pct_change * 100, 2),
        "z_score": round(z_score, 2),
        "volume_ratio": round(volume_ratio, 2),
        "is_meaningful": len(flags) > 0,
        "flags": flags,
    }
