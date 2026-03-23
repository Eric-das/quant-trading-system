from __future__ import annotations

from sqlalchemy import select

from db.models import Signal
from db.repositories.base import BaseRepository


class SignalRepository(BaseRepository):
    """
    Minimal repository for future signal persistence.
    """

    def save_signal(self, signal: Signal) -> Signal:
        return self.add(signal)

    def list_recent_signals(self, limit: int = 100) -> list[Signal]:
        statement = select(Signal).order_by(Signal.timestamp.desc()).limit(limit)
        return self.execute(statement).scalars().all()
