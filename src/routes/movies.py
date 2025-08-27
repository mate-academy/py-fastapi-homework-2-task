from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.openapi.models import Response
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from starlette import status
from starlette.status import HTTP_409_CONFLICT, HTTP_201_CREATED, HTTP_200_OK, HTTP_204_NO_CONTENT

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel

from schemas.movies import MovieListResponseSchema, MovieDetailSchema, CreateMovieSchema, MovieListItemSchema

router = APIRouter()



@router.get("/movies/", response_model=MovieListResponseSchema)
async def list_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db),
):
    total_items = await db.execute(select(func.count(MovieModel.id)))
    total_items = total_items.scalar()

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    )
    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None
    )

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )



@router.post("/movies/", response_model=MovieDetailSchema, status_code=HTTP_201_CREATED)
async def create_movie(movie: CreateMovieSchema, db: AsyncSession = Depends(get_db)):
    check_movie_name_and_date = await db.execute(select(MovieModel).where(
        MovieModel.name == movie.name,
        MovieModel.date == movie.date
    ))

    if check_movie_name_and_date.scalar():
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie.name}' "
                   f"and release date '{movie.date}' already exists."
        )

    result = await db.execute(select(CountryModel).where(CountryModel.code == movie.country))
    country = result.scalar_one_or_none()
    if not country:
        country = CountryModel(
            code=movie.country,
            name=None
        )
        db.add(country)
        await db.flush()

    genres = []
    for g in movie.genres:
        result = await db.execute(select(GenreModel).where(GenreModel.name == g))
        genre = result.scalar_one_or_none()
        if not genre:
            genre = GenreModel(
                name=g
            )
            db.add(genre)
            await db.flush()
        genres.append(genre)


    actors = []
    for a in movie.actors:
        result = await db.execute(select(ActorModel).where(ActorModel.name == a))
        actor = result.scalar_one_or_none()
        if not actor:
            actor = ActorModel(
                name=a
            )
            db.add(actor)
            await db.flush()
        actors.append(actor)

    languages = []
    for l in movie.languages:
        result = await db.execute(select(LanguageModel).where(LanguageModel.name == l))
        language = result.scalar_one_or_none()
        if not language:
            language = LanguageModel(
                name=l
            )
            db.add(language)
            await db.flush()
        languages.append(language)

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages)
        )
        .where(MovieModel.id == new_movie.id)
    )
    movie_with_relations = result.scalar_one()
    return movie_with_relations


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages)
        )
        .where(MovieModel.id == movie_id)
    )

    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    await db.delete(movie)
    await db.commit()
    return movie


@router.patch("/movies/{movie_id}/", status_code=status.HTTP_200_OK)
async def update_movie(movie_id, movie: MovieListItemSchema, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie_update = result.scalar_one_or_none()

    if not movie_update:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    movie_data = movie.dict(exclude_unset=True)

    for k, v in movie_data.items():
        setattr(movie_update, k, v)

    await db.commit()
    return {"detail": "Movie updated successfully."}