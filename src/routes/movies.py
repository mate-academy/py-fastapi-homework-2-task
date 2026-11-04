from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from database.models import (
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel
)
from schemas import (
    MovieListResponseSchema,
    MovieCreateSchema,
    MovieCreateResponseSchema,
    MovieDetailSchema,
    MovieUpdateSchema
)

router = APIRouter()


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
    status_code=200
)
async def get_movies(
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
):
    total_items = await db.scalar(
        select(func.count()).select_from(MovieModel)
    )
    total_items = total_items or 0

    offset = (page - 1) * per_page

    statement = (select(MovieModel)
                 .order_by(MovieModel.id.desc())
                 .offset(offset)
                 .limit(per_page))

    result = await db.execute(statement)
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(
            status_code=404,
            detail="No movies found.",
        )

    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages and total_items > 0:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )

    path = "/theater/movies/"
    prev_page = (
        f"{path}?page={page - 1}&per_page={per_page}"
        if page > 1
        else None
    )
    next_page = (
        f"{path}?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post(
    "/movies/",
    response_model=MovieCreateResponseSchema,
    status_code=201
)
async def create_movie(
        movie_data: MovieCreateSchema,
        db: AsyncSession = Depends(get_db)
):
    statement = select(MovieModel).where(
        MovieModel.name == movie_data.name,
        MovieModel.date == movie_data.date
    )

    existing_movie = await db.scalar(statement)

    if existing_movie is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie_data.name}' "
                f"and release date '{movie_data.date}' already exists."
            )
        )

    movie_fields = movie_data.model_dump(
        exclude={"country", "genres", "actors", "languages"}
    )
    movie = MovieModel(**movie_fields)

    genres = []

    for genre_name in dict.fromkeys(movie_data.genres):
        statement = select(GenreModel).where(
            GenreModel.name == genre_name
        )

        genre = await db.scalar(statement)

        if genre is None:
            genre = GenreModel(name=genre_name)
            db.add(genre)

        genres.append(genre)

    movie.genres = genres

    actors = []

    for actor_name in dict.fromkeys(movie_data.actors):
        statement = select(ActorModel).where(
            ActorModel.name == actor_name
        )

        actor = await db.scalar(statement)

        if actor is None:
            actor = ActorModel(name=actor_name)
            db.add(actor)

        actors.append(actor)

    movie.actors = actors

    languages = []

    for movie_language in dict.fromkeys(movie_data.languages):
        statement = select(LanguageModel).where(
            LanguageModel.name == movie_language
        )

        language = await db.scalar(statement)

        if language is None:
            language = LanguageModel(name=movie_language)
            db.add(language)

        languages.append(language)

    movie.languages = languages

    statement = select(CountryModel).where(
        CountryModel.code == movie_data.country
    )

    country = await db.scalar(statement)

    if country is None:
        country = CountryModel(code=movie_data.country)
        db.add(country)

    movie.country = country

    db.add(movie)

    try:
        await db.commit()
        await db.refresh(movie)

        statement = (
            select(MovieModel)
            .options(
                selectinload(MovieModel.country),
                selectinload(MovieModel.genres),
                selectinload(MovieModel.actors),
                selectinload(MovieModel.languages),
            )
            .where(MovieModel.id == movie.id)
        )

        return await db.scalar(statement)

    except IntegrityError as exc:
        await db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie_data.name}' "
                f"and release date '{movie_data.date}' already exists."
            ),
        ) from exc

    except SQLAlchemyError as exc:
        await db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Database operation failed.",
        ) from exc


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema, status_code=200)
async def get_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    statement = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )

    movie = await db.scalar(statement)

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )

    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    movie = await db.get(MovieModel, movie_id)

    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    try:
        await db.delete(movie)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database operation failed",
        )


@router.patch("/movies/{movie_id}/", status_code=200)
async def update_movie(
    movie_id: int,
    fields_to_update: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    movie = await db.get(MovieModel, movie_id)

    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    update_data = fields_to_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(movie, field, value)

    try:
        await db.commit()
        return {"detail": "Movie updated successfully."}
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database operation failed",
        )
