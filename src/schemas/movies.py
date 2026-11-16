import datetime
from pydantic import BaseModel, ConfigDict

from pagination.schemas import BaseListPaginationSchema


class MovieListObjectResponse(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseListPaginationSchema):
    movies: list[MovieListObjectResponse]
