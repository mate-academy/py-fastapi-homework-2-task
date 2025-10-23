import os
from pathlib import Path
from typing import Any
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv


BASE_DIR = Path(__file__).parent.parent
dotenv_path = BASE_DIR / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)


class BaseAppSettings(BaseSettings):
    BASE_DIR: Path = Path(__file__).parent.parent
    PATH_TO_DB: str = str(BASE_DIR / "database" / "source" / "theater.db")
    PATH_TO_MOVIES_CSV: str = str(
        BASE_DIR / "database" / "seed_data" / "imdb_movies.csv"
    )

    model_config = {
        "env_file": dotenv_path,
        "env_file_encoding": "utf-8",
        "extra": "allow",
    }


class Settings(BaseAppSettings):
    POSTGRES_USER: str = Field(..., env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(..., env="POSTGRES_PASSWORD")
    POSTGRES_HOST: str = Field(..., env="POSTGRES_HOST")
    POSTGRES_DB_PORT: int = Field(..., ge=1, le=65535, env="POSTGRES_DB_PORT")
    POSTGRES_DB: str = Field(..., env="POSTGRES_DB")


class TestingSettings(BaseAppSettings):
    def model_post_init(self, __context: dict[str, Any] | None = None) -> None:
        object.__setattr__(self, "PATH_TO_DB", ":memory:")
        object.__setattr__(
            self,
            "PATH_TO_MOVIES_CSV",
            str(self.BASE_DIR / "database" / "seed_data" / "test_data.csv"),
        )


def get_settings() -> BaseAppSettings:
    """
    Returns the settings for the project.
    If ENVIRONMENT=testing, returns TestingSettings.
    Otherwise, returns Settings that read .env.
    """
    environment = os.getenv("ENVIRONMENT", "developing")
    if environment.lower() == "testing":
        return TestingSettings()
    return Settings()
