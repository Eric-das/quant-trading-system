from __future__ import annotations

import pandas as pd
from sqlalchemy import select

from db.engine import get_engine
from db.models import PriceBar
from services.clean_data import clean_price_data


def load_price_data(symbol: str) -> pd.DataFrame:
    """
    Load raw price bars for a symbol, apply the clean layer, and return the
    minimal strategy input frame sorted by timestamp ascending.
    """
    statement = (
        select(
            PriceBar.timestamp,
            PriceBar.close,
            PriceBar.symbol,
            PriceBar.source,
        )
        .where(PriceBar.symbol == symbol.upper())
        .order_by(PriceBar.timestamp.asc())
    )

    with get_engine().connect() as connection:
        df = pd.read_sql(statement, connection)

    cleaned = clean_price_data(df)
    result = cleaned.loc[:, ["timestamp", "close"]].sort_values("timestamp").reset_index(drop=True)
    return result
