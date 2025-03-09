from crud.base import Base
from database import models


class CountryDB(Base):
    model = models.CountryModel
