from __future__ import annotations

import argparse
from decimal import Decimal
from pathlib import Path
import sys

import pandas as pd
from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.fetch_yfinance import STANDARD_COLUMNS, fetch_price_data
from db.engine import get_session_factory
from db.models import PriceBar


SessionLocal = get_session_factory()


def to_decimal(value) -> Decimal:
    """Convert pandas/numpy numeric values into Decimal for Numeric columns."""
    return Decimal(str(value))


def load_price_data_from_csv(csv_path: str | None) -> pd.DataFrame:
    """Load already-normalized price data from a local CSV file for offline tests."""
    if not csv_path:
        return pd.DataFrame(columns=STANDARD_COLUMNS)

    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV fallback file not found: {path}")

    print(f"[loader] loading fallback CSV from {path}")
    frame = pd.read_csv(path)
    print(f"[loader] csv shape={frame.shape}")
    print(f"[loader] csv columns={list(frame.columns)}")

    missing_columns = sorted(set(STANDARD_COLUMNS) - set(frame.columns))
    if missing_columns:
        raise ValueError(f"CSV fallback is missing required columns: {missing_columns}")

    frame = frame[STANDARD_COLUMNS].copy()
    frame["symbol"] = frame["symbol"].astype(str).str.upper()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)

    return frame.sort_values("timestamp").reset_index(drop=True)


def load_symbol(
    symbol: str = "NVDA",
    period: str = "6mo",
    interval: str = "1d",
    csv_path: str | None = None,
) -> None:
    """Fetch daily Yahoo Finance data and insert only missing rows."""
    if interval != "1d":
        raise ValueError("This loader currently supports only daily ('1d') bars.")

    print(f"[loader] symbol={symbol.upper()} period={period} interval={interval}")
    price_data = fetch_price_data(symbol=symbol, period=period, interval=interval)
    source_name = "yfinance"

    if price_data.empty and csv_path:
        print("[loader] yahoo returned no rows, using CSV fallback")
        price_data = load_price_data_from_csv(csv_path)
        source_name = "csv"

    if price_data.empty:
        print(f"No price data returned for {symbol}.")
        return

    inserted = 0
    skipped = 0

    with SessionLocal() as session:
        existing_timestamps = set(
            session.execute(
                select(PriceBar.timestamp).where(
                    PriceBar.symbol == symbol.upper(),
                )
            )
            .scalars()
            .all()
        )

        for row in price_data.itertuples(index=False):
            timestamp = row.timestamp.to_pydatetime()
            if timestamp in existing_timestamps:
                skipped += 1
                continue

            session.add(
                PriceBar(
                    symbol=row.symbol,
                    timeframe=interval,
                    timestamp=timestamp,
                    open=to_decimal(row.open),
                    high=to_decimal(row.high),
                    low=to_decimal(row.low),
                    close=to_decimal(row.close),
                    volume=to_decimal(row.volume),
                    source=source_name,
                )
            )
            inserted += 1

        session.commit()

    print(f"Symbol: {symbol.upper()}")
    print(f"Source: {source_name}")
    print(f"Inserted rows: {inserted}")
    print(f"Skipped rows: {skipped}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load daily price data into PostgreSQL.")
    parser.add_argument("--symbol", default="NVDA", help="Ticker symbol to fetch, for example AAPL")
    parser.add_argument("--period", default="6mo", help="Yahoo Finance period, for example 1mo or 6mo")
    parser.add_argument("--interval", default="1d", help="Yahoo Finance interval, currently only 1d is supported")
    parser.add_argument("--csv", default=None, help="Optional CSV fallback with columns: symbol,timestamp,open,high,low,close,volume")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    load_symbol(
        symbol=args.symbol,
        period=args.period,
        interval=args.interval,
        csv_path=args.csv,
    )
