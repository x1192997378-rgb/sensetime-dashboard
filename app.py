from datetime import datetime
from typing import Any

import yfinance as yf
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates


SYMBOL = "0020.HK"  # 商汤-W

app = FastAPI(title="SenseTime Realtime Dashboard")
templates = Jinja2Templates(directory="templates")


def _to_float(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def get_realtime_payload() -> dict[str, Any]:
    ticker = yf.Ticker(SYMBOL)

    # 1m 级别日内数据。yfinance 的港股数据通常存在延迟，但足够用于作品集演示。
    intraday = ticker.history(period="1d", interval="1m")
    if intraday.empty:
        return {
            "symbol": SYMBOL,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "quote": {"price": 0.0, "change": 0.0, "change_percent": 0.0},
            "series": {"labels": [], "volume": [], "amount": []},
            "note": "No intraday data returned from provider.",
        }

    intraday = intraday.dropna(subset=["Close", "Volume"])
    intraday["Amount"] = intraday["Close"] * intraday["Volume"]

    labels = [idx.strftime("%H:%M") for idx in intraday.index.to_pydatetime()]
    volume_series = [int(v) for v in intraday["Volume"].tolist()]
    amount_series = [round(float(a), 2) for a in intraday["Amount"].tolist()]

    last_close = _to_float(intraday["Close"].iloc[-1])
    prev_close = _to_float(intraday["Close"].iloc[-2]) if len(intraday) > 1 else last_close
    price_change = last_close - prev_close
    change_percent = (price_change / prev_close * 100) if prev_close else 0.0

    return {
        "symbol": SYMBOL,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "quote": {
            "price": round(last_close, 3),
            "change": round(price_change, 3),
            "change_percent": round(change_percent, 2),
        },
        "series": {
            "labels": labels,
            "volume": volume_series,
            "amount": amount_series,
        },
        "note": "Data source: Yahoo Finance (may be delayed).",
    }


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "symbol": SYMBOL})


@app.get("/api/realtime")
def realtime():
    try:
        payload = get_realtime_payload()
        return JSONResponse(payload)
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to fetch realtime data.",
                "detail": str(exc),
                "symbol": SYMBOL,
                "updated_at": datetime.now().isoformat(timespec="seconds"),
            },
        )
