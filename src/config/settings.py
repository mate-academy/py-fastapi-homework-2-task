import os
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings


API_V1_PREFIX = "/api/v1"

BASE_DIR = Path(__file__).parent.parent.parent


class BaseAppSettings(BaseSettings):
    BASE_DIR: Path = BASE_DIR
    PATH_TO_DB: str = str(BASE_DIR / "database" / "source" / "theater.db")
    PATH_TO_MOVIES_CSV: str = str(BASE_DIR / "database" / "seed_data" / "imdb_movies.csv")


class Settings(BaseAppSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_DB_PORT: int
    POSTGRES_DB: str

    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"


class TestingSettings(BaseAppSettings):

    def model_post_init(self, __context: dict[str, Any] | None = None) -> None:
        object.__setattr__(self, "PATH_TO_DB", ":memory:")
        object.__setattr__(
            self,
            "PATH_TO_MOVIES_CSV",
            str(self.BASE_DIR / "database" / "seed_data" / "test_data.csv")
        )


def get_settings() -> BaseSettings:
    environment = os.getenv("ENVIRONMENT", "developing")
    if environment == "testing":
        return TestingSettings()
    return Settings()
