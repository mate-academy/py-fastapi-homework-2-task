from fastapi import APIRouter, HTTPException, Query, Body, Path
from fastapi.params import Depends
from starlette import status
from sqlalchemy import select, func, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieListItemSchema, MovieDetailSchema, MovieCreateSchema, MovieResponseSchema, \
    MovieUpdateSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListItemSchema, status_code=status.HTTP_200_OK)
async def get_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * per_page
    query = select(MovieModel).offset(offset).limit(per_page).order_by(desc(MovieModel.id))
    result = await db.execute(query)
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")

    total_movies = await db.scalar(select(func.count(MovieModel.id)))
    total_pages = (total_movies + per_page - 1) // per_page

    if not total_movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    return {

        "movies": [MovieDetailSchema.model_validate(movie, from_attributes=True) for movie in movies],
        "prev_page": (
            f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
        ),
        "next_page": (
            f"/theater/movies/?page={page + 1}&per_page={per_page}"
            if page < total_pages
            else None
        ),
        "total_pages": total_pages,
        "total_items": total_movies,

    }


@router.post("/movies/", response_model=MovieResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(db: AsyncSession = Depends(get_db), movie: MovieCreateSchema = Body(...)):
    query = select(MovieModel).filter(
        MovieModel.name == movie.name,
        MovieModel.date == movie.date
    )
    result = await db.execute(query)
    movie_exists = result.scalar_one_or_none()

    if movie_exists:
        raise HTTPException(
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
            status_code=status.HTTP_409_CONFLICT
        )
    try:
        country_query = select(CountryModel).filter(CountryModel.code == movie.country)
        result = await db.execute(country_query)
        country_exists = result.scalar_one_or_none()
        if not country_exists:
            new_country = CountryModel(
                code=movie.country,
                name=movie.country
            )
            db.add(new_country)
            await db.flush()
            country_exists = new_country

        genres = []
        for genre in movie.genres:
            genre_query = select(GenreModel).filter(GenreModel.name == genre)
            result = await db.execute(genre_query)
            genre_exists = result.scalar_one_or_none()
            if not genre_exists:
                new_genre = GenreModel(
                    name=genre
                )
                db.add(new_genre)
                await db.flush()
                genre_exists = new_genre
            genres.append(genre_exists)

        actors = []
        for actor in movie.actors:
            actor_query = select(ActorModel).filter(ActorModel.name == actor)
            result = await db.execute(actor_query)
            actor_exists = result.scalar_one_or_none()
            if not actor_exists:
                new_actor = ActorModel(
                    name=actor
                )
                db.add(new_actor)
                await db.flush()
                actor_exists = new_actor
            actors.append(actor_exists)

        languages = []
        for language in movie.languages:
            language_query = select(LanguageModel).filter(LanguageModel.name == language)
            result = await db.execute(language_query)
            language_exists = result.scalar_one_or_none()
            if not language_exists:
                new_language = LanguageModel(
                    name=language
                )
                db.add(new_language)
                await db.flush()
                language_exists = new_language
            languages.append(language_exists)

        new_movie = MovieModel(
            name=movie.name,
            date=movie.date,
            score=movie.score,
            overview=movie.overview,
            status=movie.status,
            budget=movie.budget,
            revenue=movie.revenue,
            country=country_exists,
            genres=genres,
            actors=actors,
            languages=languages
        )
        db.add(new_movie)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(detail="Input data is invalid", status_code=status.HTTP_400_BAD_REQUEST)

    return MovieResponseSchema.model_validate(new_movie, from_attributes=True)


@router.get("/movies/{movie_id}/")
async def retrieve_movie(movie_id: int = Path(gt=0), db: AsyncSession = Depends(get_db)):
    query = select(MovieModel).options(selectinload(MovieModel.country), selectinload(MovieModel.genres),
                                       selectinload(MovieModel.actors), selectinload(MovieModel.languages)).filter(
        MovieModel.id == movie_id)
    result = await db.execute(query)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(detail="Movie with the given ID was not found.", status_code=status.HTTP_404_NOT_FOUND)

    return MovieResponseSchema.model_validate(movie, from_attributes=True)


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int = Path(gt=0), db: AsyncSession = Depends(get_db)):
    query = select(MovieModel).filter(
        MovieModel.id == movie_id)
    result = await db.execute(query)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()
    return


@router.patch("/movies/{movie_id}/", status_code=status.HTTP_200_OK)
async def update_movie(movie_id: int = Path(gt=0), db: AsyncSession = Depends(get_db),
                       movie_data: MovieUpdateSchema = Body(...)):
    query = select(MovieModel).filter(
        MovieModel.id == movie_id)
    result = await db.execute(query)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    update = movie_data.model_dump(exclude_unset=True)

    for k, v in update.items():
        if k == "date" and v is None:
            continue
        setattr(movie, k, v)

    await db.commit()
    await db.refresh(movie)

    return {"detail": "Movie updated successfully."}
