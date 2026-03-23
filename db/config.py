from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: int
    name: str
    user: str
    password: str

    @property
    def url(self) -> str:
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )


def load_database_settings(env_path: Path = ENV_PATH) -> DatabaseSettings:
    load_dotenv(dotenv_path=env_path)

    values = {
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
        "name": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    }

    missing = [key.upper() for key, value in values.items() if not value]
    if missing:
        missing_names = ", ".join(f"DB_{name}" for name in missing)
        raise ValueError(f"Missing database environment variables: {missing_names}")

    return DatabaseSettings(
        host=values["host"],
        port=int(values["port"]),
        name=values["name"],
        user=values["user"],
        password=values["password"],
    )
