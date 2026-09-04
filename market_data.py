"""
Wraps the external market data source.

Kept as a single function with a clean return contract (dict or None) so that
swapping the data source later — or adding a fallback provider if this one is
rate-limited or down — only means changing this file, nothing that calls it.
"""

import statistics

import yfinance as yf


def fetch_quote(symbol: str) -> dict | None:
    """
    Returns a dict with the latest price plus enough recent history to judge
    whether today's move is normal or unusual for THIS stock:

        price                    latest close
        prev_close               previous close (for day's % change)
        volume                   latest day's volume
        avg_volume_30d           30-day average volume (volume-spike baseline)
        daily_return_stdev_30d   volatility baseline (for the z-score check)

    Returns None if the fetch fails or there isn't enough history — callers
    must handle that as "data unavailable," not silently show stale data.
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1mo")
        if hist.empty or len(hist) < 2:
            # Fallback: request a shorter explicit interval before declaring
            # the quote unavailable.
            hist = ticker.history(period="5d", interval="1d")
        if hist.empty or len(hist) < 2:
            return None

        closes = hist["Close"].tolist()
        volumes = hist["Volume"].tolist()

        latest_price = float(closes[-1])
        prev_close = float(closes[-2])

        # Baseline history excludes today: we're judging today's move against
        # what was "normal" BEFORE today, not against a baseline that already
        # contains today's own move (that self-reference dampens the z-score
        # right when a stock is actually moving).
        hist_closes = closes[:-1]
        hist_volumes = volumes[:-1]

        returns = [
            (hist_closes[i] - hist_closes[i - 1]) / hist_closes[i - 1]
            for i in range(1, len(hist_closes))
            if hist_closes[i - 1] != 0
        ]
        stdev = statistics.stdev(returns) if len(returns) > 1 else 0.0

        avg_volume = sum(hist_volumes) / len(hist_volumes) if hist_volumes else 0.0
        latest_volume = int(volumes[-1]) if volumes else 0

        return {
            "price": latest_price,
            "prev_close": prev_close,
            "volume": latest_volume,
            "avg_volume_30d": avg_volume,
            "daily_return_stdev_30d": stdev,
        }
    except Exception as exc:  # noqa: BLE001 — any failure degrades to "unavailable"
        print(f"[market_data] fetch failed for {symbol}: {exc}")
        return None
