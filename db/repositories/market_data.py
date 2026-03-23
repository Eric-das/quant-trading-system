from __future__ import annotations

from sqlalchemy import select

from db.models import PriceBar
from db.repositories.base import BaseRepository


class MarketDataRepository(BaseRepository):
    """
    Minimal repository for future market data persistence.
    """

    def save_price_bar(self, price_bar: PriceBar) -> PriceBar:
        return self.add(price_bar)

    def list_recent_prices(self, limit: int = 100) -> list[PriceBar]:
        statement = select(PriceBar).order_by(PriceBar.timestamp.desc()).limit(limit)
        return self.execute(statement).scalars().all()
