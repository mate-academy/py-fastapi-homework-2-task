from crud.base import Base
from database import models


class LanguageDB(Base):
    model = models.LanguageModel
