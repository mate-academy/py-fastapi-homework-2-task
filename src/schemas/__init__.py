from .actors import ActorSchema, ActorDetailSchema
from .countries import CountrySchema, CountryDetailSchema
from .genres import GenreSchema, GenreDetailSchema
from .movies import (
    MovieDetailSchema,
    MovieListSchema,
    MovieListResponseSchema,
    MovieCreateSchema
)
from .languages import LanguageSchema


__all__ = [
    "ActorSchema",
    "ActorDetailSchema",
    "CountrySchema",
    "CountryDetailSchema",
    "GenreSchema",
    "GenreDetailSchema",
    "MovieCreateSchema",
    "MovieDetailSchema",
    "MovieListSchema",
    "MovieListResponseSchema",
    "LanguageSchema",
]
