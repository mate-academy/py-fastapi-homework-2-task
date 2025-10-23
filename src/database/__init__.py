import os

from .models import Base, MovieModel

environment = os.getenv("ENVIRONMENT", "developing")

if environment == "testing":
    from .session_sqlite import (
        get_sqlite_db_contextmanager as get_db_contextmanager,
        get_sqlite_db as get_db,
        reset_sqlite_database as reset_database,
    )
else:
    from .session_postgresql import (
        get_postgresql_db_contextmanager as get_db_contextmanager,
        get_postgresql_db as get_db,
    )
