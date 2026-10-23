import os

from src.database.models import Base, MovieModel

environment = os.getenv("ENVIRONMENT", "developing")

if environment == "testing":
    from src.database.session_sqlite import (
        sqlite_engine as engine,
        get_sqlite_db_contextmanager as get_db_contextmanager,
        get_sqlite_db as get_db,
        reset_sqlite_database as reset_database,
    )
else:
    from src.database.session_postgresql import (
        postgresql_engine as engine,
        get_postgresql_db_contextmanager as get_db_contextmanager,
        get_postgresql_db as get_db,
    )
