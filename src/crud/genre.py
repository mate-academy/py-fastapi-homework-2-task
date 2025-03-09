from crud.base import Base
from database import models


class GenreDB(Base):
    model = models.GenreModel
