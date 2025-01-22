from datetime import datetime, date, timedelta
from typing import Optional, List

from pydantic import BaseModel, Field, validator


class CountrySchema(BaseModel):
    name: str


class GenreSchema(BaseModel):
    name: str


class ActorSchema(BaseModel):
    name: str


class LanguageSchema(BaseModel):
    name: str


class MovieBaseSchema(BaseModel):
    name: str = Field(max_length=255, description="Название фильма (не более 255 символов)")
    date: datetime.date
    score: Optional[float] = Field(ge=0, le=100, description="Оценка (0-100)")
    genre: Optional[str]
    overview: Optional[str]
    crew: Optional[str]
    orig_title: Optional[str]
    status: Optional[str]
    orig_lang: Optional[str]
    budget: Optional[int] = Field(ge=0, description="Бюджет (не может быть отрицательным)")
    revenue: Optional[float] = Field(ge=0, description="Доход (не может быть отрицательным)")
    country: Optional[str]


class MovieCreateSchema(MovieBaseSchema):
    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]

    @validator("release_date")
    def validate_date(cls, value):
        max_date = date.today() + timedelta(days=365)
        if value > max_date:
            raise ValueError("Дата выхода не может превышать текущую дату более чем на 1 год.")
        return value


class MovieUpdateSchema(MovieBaseSchema):
    pass


class MovieReadSchema(MovieBaseSchema):
    id: int = Field(ge=0)
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]

    class Config:
        from_attributes = True
