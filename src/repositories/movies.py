import datetime

from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.elements import UnaryExpression

from database import MovieModel, get_db
from repositories.actors import ActorRepository
from repositories.countries import CountryRepository
from repositories.genres import GenreRepository
from repositories.languages import LanguageRepository
from schemas.movies import MovieCreateSchema

from .interfaces import IAsyncRepository


class MovieRepository(IAsyncRepository):
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def is_exist(self, *args) -> bool:
        object = await self.get_object(*args)
        return bool(object)

    async def get_total(self) -> int:
        return await self.db.scalar(select(func.count()).select_from(MovieModel))

    async def get_object(self, *args) -> MovieModel | None:
        return await self.db.scalar(
            select(MovieModel)
            .where(*args)
            .options(
                joinedload(MovieModel.country),
                joinedload(MovieModel.genres),
                joinedload(MovieModel.actors),
                joinedload(MovieModel.languages),
            )
        )

    async def get_object_or_404(self, *args) -> MovieModel:
        movie = await self.get_object(*args)
        if movie is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Movie with the given ID was not found.",
            )
        return movie

    async def get_objects(
        self,
        *args,
        offset: int = 0,
        limit: int = 10,
        ordering: UnaryExpression | None = None,
    ) -> list[MovieModel]:
        return await self.db.scalars(
            select(MovieModel)
            .where(*args)
            .order_by(ordering)
            .offset(offset)
            .limit(limit)
        )

    async def get_objects_or_404(
        self,
        *args,
        offset: int = 0,
        limit: int = 10,
        ordering: UnaryExpression | None = None,
    ) -> list[MovieModel]:
        movies = await self.get_objects(*args, offset=offset, limit=limit, ordering=ordering)
        if not movies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No movies found.",
            )
        return movies

    async def create_object(self, data: MovieCreateSchema) -> MovieModel:
        country_repo = CountryRepository(self.db)
        genre_repo = GenreRepository(self.db)
        actor_repo = ActorRepository(self.db)
        language_repo = LanguageRepository(self.db)

        async with self.db.begin_nested():
            country = await country_repo.get_or_create(data.country, commit=False)

            genres = [await genre_repo.get_or_create(name, commit=False) for name in data.genres]
            actors = [await actor_repo.get_or_create(name, commit=False) for name in data.actors]
            languages = [await language_repo.get_or_create(name, commit=False) for name in data.languages]

            movie = MovieModel(
                name=data.name,
                date=data.date,
                score=data.score,
                overview=data.overview,
                status=data.status,
                budget=data.budget,
                revenue=data.revenue,
                country=country,
                genres=genres,
                actors=actors,
                languages=languages,
            )

            self.db.add(movie)

        await self.db.refresh(movie)
        return movie

    async def delete_object(self, *args, raise_exception: bool = False) -> bool:
        if raise_exception:
            movie = await self.get_object_or_404(*args)
        else:
            movie = await self.get_object(*args)
            if not movie:
                return False

        await self.db.delete(movie)
        await self.db.commit()
        return True

    async def update_object(self, *args: int, data: dict = {}, raise_exception: bool = False) -> bool:
        if raise_exception:
            movie = await self.get_object_or_404(*args)
        else:
            movie = await self.get_object(*args)
            if not movie:
                return False

        for key, value in data.items():
            if hasattr(movie, key):
                setattr(movie, key, value)

        await self.db.commit()
        await self.db.refresh(movie)
        return True


async def get_movie_repository(
    db: AsyncSession = Depends(get_db),
) -> MovieRepository:
    return MovieRepository(db)
