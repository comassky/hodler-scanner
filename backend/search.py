"""Ticker search (name / symbol / ISIN) via Yahoo Finance."""
import re

import yfinance as yf

# Relevance order for search results (lower = shown first).
_QUOTE_TYPE_RANK = {
    "EQUITY": 0,
    "ETF": 1,
    "INDEX": 2,
    "MUTUALFUND": 3,
    "CRYPTOCURRENCY": 4,
    "CURRENCY": 5,
    "FUTURE": 6,
}


def search_tickers(q: str) -> list[dict]:
    """
    Search Yahoo Finance by company name, ticker symbol or **ISIN**
    (e.g. ``Apple``, ``MC.PA``, ``FR0000121014``). Fuzzy matching tolerates typos.
    """
    q = q.strip()
    if len(q) < 2:
        return []

    try:
        quotes = yf.Search(q, max_results=15, enable_fuzzy_query=True).quotes
    except TypeError:
        # Older yfinance without the fuzzy flag
        quotes = yf.Search(q, max_results=15).quotes
    except Exception:
        return []

    ql = q.lower()
    seen: set[str] = set()
    items: list[dict] = []
    for r in quotes:
        sym = (r.get("symbol") or "").strip()
        name = (r.get("longname") or r.get("shortname") or "").strip()
        name = re.sub(r"\s{2,}", " ", name)   # collapse Yahoo's internal padding
        if not sym or not name or sym in seen:
            continue
        seen.add(sym)
        qtype = r.get("quoteType", "")
        base = sym.lower().split(".")[0]
        items.append({
            "ticker":   sym,
            "name":     name,
            "type":     r.get("typeDisp") or qtype.title(),
            "exchange": r.get("exchDisp", ""),
            "_exact":   0 if ql in (sym.lower(), base) else 1,
            "_rank":    _QUOTE_TYPE_RANK.get(qtype, 9),
        })

    # Exact symbol/ISIN matches first, then equities & ETFs above exotic types;
    # Yahoo's own relevance order is preserved within each group (stable sort).
    items.sort(key=lambda x: (x["_exact"], x["_rank"]))
    for x in items:
        del x["_exact"], x["_rank"]
    return items[:10]
