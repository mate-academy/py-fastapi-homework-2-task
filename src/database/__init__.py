from .models import (
    Base,
    MovieModel,
    GenreModel,
    ActorModel,
    CountryModel,
    LanguageModel,
)

from .session_sqlite import (
    init_db,
    close_db,
    get_db,
    get_sqlite_db_contextmanager as get_db_contextmanager,
    reset_sqlite_database,
    reset_database,
)

try:
    from .populate import CSVDatabaseSeeder  # noqa: F401
except Exception:
    CSVDatabaseSeeder = None  # optional

__all__ = [
    # models
    "Base",
    "MovieModel",
    "GenreModel",
    "ActorModel",
    "CountryModel",
    "LanguageModel",
    # session / init
    "init_db",
    "close_db",
    "get_db",
    "get_db_contextmanager",
    "reset_sqlite_database",
    "reset_database",
    # optional seeder
    "CSVDatabaseSeeder",
]
