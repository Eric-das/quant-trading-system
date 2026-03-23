from db.engine import get_engine
from db.models import Base


def create_all_tables() -> None:
    Base.metadata.create_all(bind=get_engine())


def recreate_all_tables() -> None:
    Base.metadata.drop_all(bind=get_engine())
    Base.metadata.create_all(bind=get_engine())


if __name__ == "__main__":
    create_all_tables()
