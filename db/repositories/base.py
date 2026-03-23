from __future__ import annotations

from sqlalchemy.orm import Session


class BaseRepository:
    """
    Lightweight base repository.

    Keeps shared session access in one place without adding business rules.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, instance: object) -> object:
        self.session.add(instance)
        return instance

    def execute(self, statement):
        return self.session.execute(statement)
