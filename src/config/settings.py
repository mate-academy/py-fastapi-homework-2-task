# src/config/settings.py
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings


class BaseAppSettings(BaseSettings):
    BASE_DIR: Path = Path(__file__).resolve().parents[1]
    PATH_TO_DB: str = str(BASE_DIR / "database" / "source" / "theater.db")
    PATH_TO_MOVIES_CSV: str = str(BASE_DIR / "database" / "seed_data" / "imdb_movies.csv")


class Settings(BaseAppSettings):
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "test_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "test_password")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "test_host")
    POSTGRES_DB_PORT: int = int(os.getenv("POSTGRES_DB_PORT", 5432))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "test_db")


class TestingSettings(BaseAppSettings):
    def model_post_init(self, __context: dict[str, Any] | None = None) -> None:  # type: ignore[override]
        object.__setattr__(self, "PATH_TO_DB", ":memory:")
        object.__setattr__(
            self,
            "PATH_TO_MOVIES_CSV",
            str(self.BASE_DIR / "database" / "seed_data" / "test_data.csv"),
        )


@lru_cache
def get_settings() -> BaseAppSettings:
    env = os.getenv("ENVIRONMENT", "developing").lower()
    testing_flag = os.getenv("TESTING", "0") in ("1", "true", "True")
    if env == "testing" or testing_flag:
        return TestingSettings()
    return Settings()
