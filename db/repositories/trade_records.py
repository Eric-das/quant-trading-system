from __future__ import annotations

from sqlalchemy import select

from db.models import TradeRecord
from db.repositories.base import BaseRepository


class TradeRecordRepository(BaseRepository):
    """
    Minimal repository for future trade record persistence.
    """

    def save_trade_record(self, trade_record: TradeRecord) -> TradeRecord:
        return self.add(trade_record)

    def list_recent_trades(self, limit: int = 100) -> list[TradeRecord]:
        statement = select(TradeRecord).order_by(TradeRecord.created_at.desc()).limit(limit)
        return self.execute(statement).scalars().all()
