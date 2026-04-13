from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import investpy
import pandas as pd
import yfinance as yf


DATA_DIR = Path("data")
CSV_PATH = DATA_DIR / "stock_history.csv"
DB_PATH = DATA_DIR / "stock_history.db"


def fetch_history(symbol: str, lookback_days: int = 30) -> pd.DataFrame:
    """
    Fetch recent historical daily K-line data.
    Primary source: Investing.com via investpy.
    Fallback source: Yahoo Finance via yfinance.
    """
    stock_code = symbol.split(".")[0]
    from_date = (datetime.today() - timedelta(days=max(lookback_days * 3, 90))).strftime("%d/%m/%Y")
    to_date = datetime.today().strftime("%d/%m/%Y")

    try:
        raw = investpy.get_stock_historical_data(
            stock=stock_code,
            country="hong kong",
            from_date=from_date,
            to_date=to_date,
        )
        if not raw.empty:
            df = raw.reset_index()[["Date", "Open", "High", "Low", "Close", "Volume"]]
            return df.tail(lookback_days).copy()
    except Exception:
        pass

    # Fallback for demo reliability.
    ticker = yf.Ticker(symbol)
    raw_yf = ticker.history(period="3mo", interval="1d")
    if raw_yf.empty:
        raise ValueError(f"No data returned from Investing.com or Yahoo for symbol: {symbol}")

    df_yf = raw_yf.reset_index()[["Date", "Open", "High", "Low", "Close", "Volume"]]
    return df_yf.tail(lookback_days).copy()


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned["Date"] = pd.to_datetime(cleaned["Date"]).dt.date

    numeric_cols = ["Open", "High", "Low", "Close", "Volume"]
    for col in numeric_cols:
        cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")

    # Fill missing values by nearest known value first, then fallback to zero.
    cleaned[numeric_cols] = cleaned[numeric_cols].ffill().bfill().fillna(0)

    cleaned["Volume"] = cleaned["Volume"].round(0).astype(int)
    cleaned = cleaned.sort_values("Date").reset_index(drop=True)
    return cleaned


def add_features(df: pd.DataFrame, sma_window: int = 5, ema_span: int = 12) -> pd.DataFrame:
    featured = df.copy()
    featured["daily_return"] = featured["Close"].pct_change().fillna(0.0)
    featured["SMA"] = featured["Close"].rolling(window=sma_window, min_periods=1).mean()
    featured["EMA"] = featured["Close"].ewm(span=ema_span, adjust=False).mean()
    return featured


def analyze_up_days_ratio(df: pd.DataFrame, threshold: float = 0.03) -> float:
    if df.empty:
        return 0.0
    ratio = (df["daily_return"] > threshold).sum() / len(df)
    return float(ratio)


def persist_data(df: pd.DataFrame, symbol: str) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    df_to_save = df.copy()
    df_to_save["symbol"] = symbol
    df_to_save.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

    with sqlite3.connect(DB_PATH) as conn:
        df_to_save.to_sql("stock_history", conn, if_exists="replace", index=False)


def run_pipeline(symbol: str, lookback_days: int = 30, threshold: float = 0.03) -> tuple[pd.DataFrame, dict]:
    raw = fetch_history(symbol=symbol, lookback_days=lookback_days)
    cleaned = clean_data(raw)
    featured = add_features(cleaned)
    persist_data(featured, symbol)

    summary = {
        "symbol": symbol,
        "lookback_days": lookback_days,
        "avg_daily_return": float(featured["daily_return"].mean()),
        "max_daily_return": float(featured["daily_return"].max()),
        "up_days_ratio": analyze_up_days_ratio(featured, threshold=threshold),
        "latest_close": float(featured["Close"].iloc[-1]),
    }
    return featured, summary


def cron_integration_note() -> str:
    return (
        "This pipeline can be integrated with Cron/Airflow. "
        "For example, run every 6 hours to fetch new data, compute indicators, "
        "and persist to CSV/SQLite for downstream dashboards."
    )
