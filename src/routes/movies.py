from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import MovieCreateSchema
from schemas.movies import MovieListResponseSchema, MovieDetailSchema, MovieUpdateSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_all_movies(page: int = 1, per_page: int = 10, session: AsyncSession = Depends(get_db)):
    if page < 1:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["query", "page"],
                    "msg": "Input should be greater than or equal to 1",
                    "type": "value_error.number.not_ge"
                }
            ]
        )
    if per_page < 1:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["query", "per_page"],
                    "msg": "Input should be greater than or equal to 1",
                    "type": "value_error.number.not_ge"
                }
            ]
        )
    elif per_page > 20:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["query", "per_page"],
                    "msg": "Input should be less than or equal to 20",
                    "type": "value_error.number.not_le"
                }
            ]
        )

    movies = await session.scalars(
        select(MovieModel)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .order_by(MovieModel.id.desc())
    )

    result = list(movies.all())
    if len(result) == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_items = await session.scalar(select(func.count()).select_from(MovieModel))
    total_pages = (total_items + per_page - 1) // per_page
    if page > 1:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"
    else:
        prev_page = None

    if page < total_pages:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"
    else:
        next_page = None

    return {
        "movies": result,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post("/movies/", status_code=201, response_model=MovieDetailSchema)
async def create_movie(movie_data: dict, session: AsyncSession = Depends(get_db)):
    try:
        movie_data = MovieCreateSchema.model_validate(movie_data)
    except ValidationError:
        raise HTTPException(status_code=400, detail="Invalid input data.")
    movie = await session.scalar(
        select(MovieModel).
        where(
            MovieModel.name == movie_data.name,
            MovieModel.date == movie_data.date,
        )
    )
    if movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    country_code = movie_data.country
    country = await session.scalar(select(CountryModel).where(CountryModel.code == country_code))
    if country is None:
        country = CountryModel(code=country_code)
        session.add(country)
        await session.flush()

    genres = movie_data.genres
    genres_list = []
    for genre_name in genres:
        genre = await session.scalar(select(GenreModel).where(GenreModel.name == genre_name))
        if genre is None:
            genre = GenreModel(name=genre_name)
            session.add(genre)
            await session.flush()
        genres_list.append(genre)

    actors = movie_data.actors
    actors_list = []
    for actor_name in actors:
        actor = await session.scalar(select(ActorModel).where(ActorModel.name == actor_name))
        if actor is None:
            actor = ActorModel(name=actor_name)
            session.add(actor)
            await session.flush()
        actors_list.append(actor)

    languages = movie_data.languages
    languages_list = []
    for language_name in languages:
        language = await session.scalar(select(LanguageModel).where(LanguageModel.name == language_name))
        if language is None:
            language = LanguageModel(name=language_name)
            session.add(language)
            await session.flush()
        languages_list.append(language)

    movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country=country,
    )
    movie.genres = genres_list
    movie.actors = actors_list
    movie.languages = languages_list

    session.add(movie)
    await session.commit()

    movie = await session.scalar(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie.id)
    )

    return movie


@router.get("/movies/{movie_id}/", status_code=200, response_model=MovieDetailSchema)
async def get_movies_by_id(movie_id: int, session: AsyncSession = Depends(get_db)):
    movie = await session.scalar(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )

    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def get_delete_movie(movie_id: int, session: AsyncSession = Depends(get_db)):
    movie = await session.scalar(select(MovieModel).where(MovieModel.id == movie_id))
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await session.delete(movie)
    await session.commit()


@router.patch("/movies/{movie_id}/", status_code=200)
async def get_update_movie(
        movie_id: int,
        movie_data: dict,
        session: AsyncSession = Depends(get_db)
):
    try:
        movie_data = MovieUpdateSchema.model_validate(movie_data)
    except ValidationError:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    movie = await session.scalar(select(MovieModel).where(MovieModel.id == movie_id))
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    update_data = movie_data.model_dump(exclude_unset=True)

    if "name" in update_data:
        movie.name = movie_data.name
    if "date" in update_data:
        movie.date = movie_data.date
    if "score" in update_data:
        movie.score = movie_data.score
    if "overview" in update_data:
        movie.overview = movie_data.overview
    if "status" in update_data:
        movie.status = movie_data.status
    if "budget" in update_data:
        movie.budget = movie_data.budget
    if "revenue" in update_data:
        movie.revenue = movie_data.revenue

    await session.commit()

    return {"detail": "Movie updated successfully."}
