"""Portfolio valuation — enrich stored positions with live prices, P&L and weights."""
from __future__ import annotations

import db
from market_data import download_batch, flat_col


def _last_close(data) -> float | None:
    """Last available close from a (possibly empty) OHLCV frame."""
    if data is None or getattr(data, "empty", True):
        return None
    try:
        s = flat_col(data, "Close").dropna()
    except (KeyError, TypeError):
        return None
    return round(float(s.iloc[-1]), 2) if not s.empty else None


def _empty() -> dict:
    return {
        "positions": [],
        "totals": {"cost": 0.0, "value": 0.0, "pnl": 0.0, "pnl_pct": None, "count": 0, "priced": True},
    }


def build_portfolio() -> dict:
    """Return every position enriched with its live price, P&L and portfolio weight."""
    positions = db.get_positions()
    if not positions:
        return _empty()

    tickers = [p["ticker"] for p in positions]
    raw = download_batch(tickers, "5d", False)
    names = db.get_names()

    items: list[dict] = []
    total_cost = total_value = 0.0
    priced = True
    for p in positions:
        code = p["ticker"]
        qty = float(p["quantity"])
        avg = float(p["avg_cost"])
        price = _last_close(raw.get(code))
        cost = qty * avg
        value = round(qty * price, 2) if price is not None else None
        pnl = round(value - cost, 2) if value is not None else None
        pnl_pct = round(pnl / cost * 100, 2) if (pnl is not None and cost > 0) else None

        total_cost += cost
        if value is not None:
            total_value += value
        else:
            priced = False

        items.append({
            "ticker": code,
            "name": names.get(code) or code,
            "quantity": qty,
            "avg_cost": round(avg, 4),
            "price": price,
            "cost": round(cost, 2),
            "value": value,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "note": p.get("note"),
        })

    for it in items:
        it["weight"] = (
            round(it["value"] / total_value * 100, 2)
            if (it["value"] and total_value > 0) else None
        )

    total_pnl = round(total_value - total_cost, 2)
    total_pnl_pct = round(total_pnl / total_cost * 100, 2) if total_cost > 0 else None
    return {
        "positions": items,
        "totals": {
            "cost": round(total_cost, 2),
            "value": round(total_value, 2),
            "pnl": total_pnl,
            "pnl_pct": total_pnl_pct,
            "count": len(items),
            "priced": priced,
        },
    }
