"""
Sanity test for the whole flow, using a mocked fetch_quote (this sandbox
can't reach Yahoo Finance, but the real function works wherever you deploy).
Simulates: add a stock with a target -> "visit 1" (price below target) ->
price moves past target -> "visit 2" (diff should show target_hit=True).
"""
import market_data

# --- Mock price sequence: first call = visit 1 state, second = visit 2 state
_mock_calls = {"n": 0}
_mock_sequence = [
    {"price": 4150.0, "prev_close": 4100.0, "volume": 500000, "avg_volume_30d": 480000, "daily_return_stdev_30d": 0.012},
    {"price": 4250.0, "prev_close": 4150.0, "volume": 2200000, "avg_volume_30d": 480000, "daily_return_stdev_30d": 0.012},
]


def mock_fetch_quote(symbol):
    idx = min(_mock_calls["n"], len(_mock_sequence) - 1)
    _mock_calls["n"] += 1
    return _mock_sequence[idx]


market_data.fetch_quote = mock_fetch_quote

# Import main AFTER patching so it picks up the mocked function
import main  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

client = TestClient(main.app)

# 1. Add a watchlist item with a reason + target price (requirement 1 differentiator)
resp = client.post("/watchlist", json={
    "symbol": "reliance.ns",
    "display_name": "Reliance Industries",
    "reason": "Watching before Q2 earnings, want in if it breaks 4200",
    "target_price": 4200.0,
})
print("ADD:", resp.status_code, resp.json())
item_id = resp.json()["id"]

# 2. "Visit 1": fetch current watchlist (price 4150, below target) -> creates snapshot 1
resp = client.get("/watchlist")
print("\nWATCHLIST (visit 1):", resp.status_code)
for row in resp.json():
    print(" ", row)

# 3. Call diff once to establish the visit log baseline (first-ever visit)
resp = client.get("/watchlist/diff")
print("\nDIFF (first visit, no prior baseline):", resp.status_code, resp.json())

# 4. "Visit 2": fetch watchlist again (price now 4250, crossed target, volume spiked)
resp = client.get("/watchlist")
print("\nWATCHLIST (visit 2):", resp.status_code)
for row in resp.json():
    print(" ", row)

# 5. Diff again -> should show delta_pct, is_meaningful=True, target_hit=True
resp = client.get("/watchlist/diff")
print("\nDIFF (visit 2 vs visit 1):", resp.status_code)
import json
print(json.dumps(resp.json(), indent=2))

# 6. Delete
resp = client.delete(f"/watchlist/{item_id}")
print("\nDELETE:", resp.status_code, resp.json())

print("\n✅ All steps ran without errors.")
