from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request
)

from sqlalchemy import select, func, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette import status

from database import get_db, MovieModel
from database.models import (
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel
)

from src.schemas.movies import MovieCreateBaseSchem, MovieOutShort, MovieOutDetailed, MovieUpdateSchema

router = APIRouter()


@router.get("/movies/")
async def get_movies(
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20)
):
    total_items_result = await db.execute(
        select(
            func.count()
        ).select_from(
            MovieModel
        )
    )
    total_items = total_items_result.scalar()

    total_pages = (total_items + per_page - 1) // per_page
    offset = (page - 1) * per_page

    result = await db.execute(
        select(MovieModel)
        .order_by(desc(MovieModel.id))
        .offset(offset)
        .limit(per_page)
    )

    movies = result.scalars().all()

    if not movies:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )

    base_url = str(request.url.path)

    api_prefix = "/api/v1"

    if base_url.startswith(api_prefix):
        base_url = base_url[len(api_prefix):]

    def make_page_url(page_num: int) -> Optional[str]:
        if 1 <= page_num <= total_pages:
            return f"{base_url}?page={page_num}&per_page={per_page}"
        return None

    return {
        "movies": [
            MovieOutShort.model_validate(movie).model_dump()
            for movie in movies
        ],
        "prev_page": make_page_url(page - 1),
        "next_page": make_page_url(page + 1),
        "total_pages": total_pages,
        "total_items": total_items
    }


@router.get("/movies/{movie_id}/", response_model=MovieOutDetailed)
async def get_movie_details(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages)
        )
        .where(MovieModel.id == movie_id)
    )
    movie = result.unique().scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(
            MovieModel
        ).where(
            MovieModel.id == movie_id
        )
    )

    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/")
async def update_movie(
        movie_id: int,
        movie_data: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    try:
        update_data = movie_data.model_dump(
            exclude_unset=True
        )
        for field, value in update_data.items():
            setattr(movie, field, value)

        await db.commit()
        return {"detail": "Movie updated successfully."}

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid input data."
        )


@router.post("/movies/", status_code=status.HTTP_201_CREATED)
async def create_movie(
        movie_data: MovieCreateBaseSchem,
        db: AsyncSession = Depends(get_db)
):
    existing_movie = await db.scalar(
        select(MovieModel)
        .where(MovieModel.name == movie_data.name)
        .where(MovieModel.date == movie_data.date)
    )
    if existing_movie:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_data.name}' and "
                   f"release date '{movie_data.date}' already exists.",
        )

    try:
        country = await db.scalar(
            select(
                CountryModel
            ).where(
                CountryModel.name == movie_data.country
            )
        )
        if not country:
            country = CountryModel(code=movie_data.country)
            db.add(country)
            await db.flush()

        genres_objects = []

        for genre_name in movie_data.genres:
            genre = await db.scalar(
                select(
                    GenreModel
                ).where(
                    GenreModel.name == genre_name
                )
            )
            if not genre:
                genre = GenreModel(name=genre_name)
                db.add(genre)
                await db.flush()

            genres_objects.append(genre)

        actors_objects = []

        for actor_name in movie_data.actors:
            actor = await db.scalar(
                select(
                    ActorModel
                ).where(
                    ActorModel.name == actor_name
                )
            )
            if not actor:
                actor = ActorModel(name=actor_name)
                db.add(actor)
                await db.flush()

            actors_objects.append(actor)

        language_objects= []

        for language_name in movie_data.languages:
            language = await db.scalar(
                select(
                    LanguageModel
                ).where(
                    LanguageModel.name == language_name
                )
            )
            if not language:
                language = LanguageModel(name=language_name)
                db.add(language)
                await db.flush()

            language_objects.append(language)

        new_movie = MovieModel(
            name=movie_data.name,
            date=movie_data.date,
            score=movie_data.score,
            overview=movie_data.overview,
            status=movie_data.status,
            budget=movie_data.budget,
            revenue=movie_data.revenue,
            country=country,
            genres=genres_objects,
            actors=actors_objects,
            languages=language_objects,
        )
        db.add(new_movie)
        await db.commit()
        await db.refresh(
            new_movie,
            ["genres", "actors", "languages"]
        )

        return new_movie

    except IntegrityError:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The input data is invalid "
                   f"(e.g., missing required fields, invalid values)."
        )
