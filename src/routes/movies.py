import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, MovieModel
from database.models import (
    MoviesGenresModel, ActorsMoviesModel, MoviesLanguagesModel
)
from schemas import (
    MovieListResponseSchema, MovieCreateSchema, MovieDetailSchema
)
from crud.actor import ActorDB
from crud.genre import GenreDB
from crud.language import LanguageDB
from crud.country import CountryDB
from crud.movie import MovieDB
from schemas.movies import MovieUpdateSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        db: AsyncSession = Depends(get_db),
        page: int = Query(1, ge=1, description="The actual page number."),
        per_page: int = Query(
        10, ge=1, le=20, description="Count movies on page"
        )
):
    total_items = await db.scalar(select(func.count(MovieModel.id)))
    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page
    offset = (page - 1) * per_page
    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    result = (
        await db.execute(
            select(MovieModel).order_by(
                MovieModel.id.desc()
            ).offset(offset).limit(per_page))
    )
    movies = result.scalars().all()

    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}"
        if page > 1 else None
    )
    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
        if page < total_pages else None
    )

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post("/movies/", status_code=201)
async def create_movie(
        movie: MovieCreateSchema,
        db: AsyncSession = Depends(get_db),
):
    max_date = datetime.date.today() + datetime.timedelta(days=365)
    if movie.date > max_date:
        raise HTTPException(
            status_code=400,
            detail="Date cannot be more than one year in the future."
        )

    find_movie = await MovieDB.find_one_or_none(
        db, name=movie.name,
        date=movie.date
    )
    if find_movie:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name "
                f"'{movie.name}' and release date "
                f"'{movie.date}' already exists."
            ),
        )

    try:
        country_obj = await CountryDB.find_one_or_none(db, code=movie.country)
        if not country_obj:
            country_obj = await CountryDB.add(db, code=movie.country)
        new_movie = await MovieDB.add(
            db,
            name=movie.name,
            date=movie.date,
            budget=movie.budget,
            status=movie.status,
            overview=movie.overview,
            revenue=movie.revenue,
            score=movie.score,
            country_id=country_obj.id,
        )

        genres = []
        for genre in movie.genres:
            genre_obj = await GenreDB.find_one_or_none(db, name=genre)
            if not genre_obj:
                genre_obj = await GenreDB.add(db, name=genre)
            genres.append(genre_obj)
            await db.execute(
                insert(MoviesGenresModel)
                .values(movie_id=new_movie.id, genre_id=genre_obj.id)
            )

        actors = []
        for actor in movie.actors:
            actor_obj = await ActorDB.find_one_or_none(db, name=actor)
            if not actor_obj:
                actor_obj = await ActorDB.add(db, name=actor)
            actors.append(actor_obj)
            await db.execute(
                insert(ActorsMoviesModel)
                .values(movie_id=new_movie.id, actor_id=actor_obj.id)
            )

        languages = []
        for language in movie.languages:
            language_obj = await LanguageDB.find_one_or_none(db, name=language)
            if not language_obj:
                language_obj = await LanguageDB.add(db, name=language)
            languages.append(language_obj)
            await db.execute(
                insert(MoviesLanguagesModel)
                .values(movie_id=new_movie.id, language_id=language_obj.id)
            )

        await db.commit()

        response = {
            "id": new_movie.id,
            "name": new_movie.name,
            "date": new_movie.date,
            "score": new_movie.score,
            "overview": new_movie.overview,
            "status": new_movie.status.value,  # convert enum to its value
            "budget": float(new_movie.budget),
            "revenue": new_movie.revenue,
            "country": {
                "id": country_obj.id,
                "code": country_obj.code,
                "name": country_obj.name,
            },
            "genres": [{"id": g.id, "name": g.name} for g in genres],
            "actors": [{"id": a.id, "name": a.name} for a in actors],
            "languages": [
                {"id": lan.id, "name": lan.name} for lan in languages
            ],
        }
        return response
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Something went wrong.")


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
    status_code=200
)
async def get_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await MovieDB.get_movie_by_id(db, movie_id=movie_id)
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie_by_id(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    try:
        return await MovieDB.delete_movie_by_id(db, movie_id=movie_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"{e}")


@router.patch("/movies/{movie_id}/", status_code=200)
async def update_movie(
        movie_id: int,
        update_data: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db)
):
    try:
        await MovieDB.update_movie_by_id(
            db,
            movie_id=movie_id,
            update_data=update_data
        )
        return {"detail": "Movie updated successfully."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"{e}")
