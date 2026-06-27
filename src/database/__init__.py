import os
from .models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel, Base

from .session_sqlite import (
    reset_sqlite_database as reset_database,
    sqlite_engine,
    get_sqlite_db_contextmanager,
    get_sqlite_db
)

engine_sqlite = sqlite_engine

environment = os.getenv("ENVIRONMENT", "developing")

if environment == "testing":
    get_db_contextmanager = get_sqlite_db_contextmanager
    get_db = get_sqlite_db
else:
    from .session_postgresql import (
        get_postgresql_db_contextmanager,
        get_postgresql_db,
    )
    get_db_contextmanager = get_postgresql_db_contextmanager
    get_db = get_postgresql_db

__all__ = [
    "MovieModel", "CountryModel", "GenreModel", "ActorModel", "LanguageModel",
    "Base", "get_db", "get_db_contextmanager", "reset_database", "engine_sqlite"
]
