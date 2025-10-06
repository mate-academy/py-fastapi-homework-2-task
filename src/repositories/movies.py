import datetime

from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import UnaryExpression

from database import MovieModel, get_db
from repositories.actors import ActorRepository
from repositories.countries import CountryRepository
from repositories.genres import GenreRepository
from repositories.languages import LanguageRepository
from schemas.movies import MovieCreateSchema


class MovieRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_total(self) -> int:
        return await self.db.scalar(select(func.count()).select_from(MovieModel))

    async def get_movie(self, movie_id: int) -> MovieModel | None:
        return await self.db.scalar(
            select(MovieModel)
            .where(MovieModel.id == movie_id)
            .options(
                selectinload(MovieModel.country),
                selectinload(MovieModel.genres),
                selectinload(MovieModel.actors),
                selectinload(MovieModel.languages),
            )
        )

    async def is_existing(self, name: str, date: datetime.date) -> bool:
        movie = await self.db.scalar(
            select(MovieModel).where(
                MovieModel.name == name,
                MovieModel.date == date,
            )
        )
        return bool(movie)

    async def get_movie_or_404(self, movie_id: int) -> MovieModel:
        movie = await self.get_movie(movie_id)
        if movie is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Movie with the given ID was not found.",
            )
        return movie

    async def get_movies(
        self,
        offset: int = 0,
        limit: int = 10,
        ordering: UnaryExpression | None = None,
    ) -> list[MovieModel]:
        print(ordering, "   ", type(ordering))
        return await self.db.scalars(
            select(MovieModel).order_by(ordering).offset(offset).limit(limit)
        )

    async def get_movies_or_404(
        self,
        offset: int = 0,
        limit: int = 10,
        ordering: UnaryExpression | None = None,
    ) -> list[MovieModel]:
        movies = await self.get_movies(offset, limit, ordering)
        if not movies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No movies found.",
            )
        return movies

    async def create_movie(self, movie_data: MovieCreateSchema) -> MovieModel:
        country_repo = CountryRepository(self.db)
        genre_repo = GenreRepository(self.db)
        actor_repo = ActorRepository(self.db)
        language_repo = LanguageRepository(self.db)

        country = await country_repo.get_or_create(movie_data.country)

        genres = []
        for name in movie_data.genres:
            genre = await genre_repo.get_or_create(name)
            genres.append(genre)

        actors = []
        for name in movie_data.actors:
            actor = await actor_repo.get_or_create(name)
            actors.append(actor)

        languages = []
        for name in movie_data.languages:
            language = await language_repo.get_or_create(name)
            languages.append(language)

        movie = MovieModel(
            name=movie_data.name,
            date=movie_data.date,
            score=movie_data.score,
            overview=movie_data.overview,
            status=movie_data.status,
            budget=movie_data.budget,
            revenue=movie_data.revenue,
            country=country,
            genres=genres,
            actors=actors,
            languages=languages,
        )

        self.db.add(movie)

        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A movie with the same name and date already exists.",
            )

        await self.db.refresh(movie)
        return movie

    async def delete_movie(self, movie_id: int) -> bool:
        movie = await self.db.get(MovieModel, movie_id)
        if not movie:
            return False

        await self.db.delete(movie)
        await self.db.commit()
        return True

    async def update_movie(self, movie_id: int, data: dict) -> bool:
        movie = await self.db.get(MovieModel, movie_id)
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
