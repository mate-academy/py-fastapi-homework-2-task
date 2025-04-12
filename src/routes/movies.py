from math import ceil
from fastapi import status

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi.responses import Response

from database import get_db, MovieModel
from database.models import GenreModel, ActorModel, LanguageModel, CountryModel
from schemas.movies import MovieListItemSchema, MovieCreationSchema, MovieDetailSchema, MovieUpdateSchema, \
    MovieListSchema

router = APIRouter()


@router.get('/movies/', response_model=MovieListItemSchema)
async def get_movies(page: int = Query(1, ge=1), per_page: int = Query(10, ge=1, le=20),
                     db: AsyncSession = Depends(get_db)):
    offset = (page - 1) * per_page
    queryset = await db.execute(select(MovieModel)
                                .offset(offset)
                                .limit(per_page)
                                .order_by(MovieModel.id.desc()))

    result = queryset.scalars().all()
    if not result:
        raise HTTPException(status_code=404, detail='No movies found.')

    total_items = (await db.execute(func.count(MovieModel.id))).scalar()

    total_pages = ceil(total_items / per_page)

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return MovieListItemSchema.model_validate({
        "movies": [MovieListSchema.model_validate(movie) for movie in result],
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    })


@router.post('/movies/', response_model=MovieDetailSchema, status_code=201)
async def create_movie(movie: MovieCreationSchema, db: AsyncSession = Depends(get_db)):
    existing_movie = await db.scalar(select(MovieModel).where(
        MovieModel.name == movie.name,
        MovieModel.date == movie.date)
    )

    if existing_movie:
        raise HTTPException(status_code=409,
                            detail=f"A movie with the name '{movie.name}' and "
                                   f"release date '{movie.date}' already exists.")

    try:
        existing_country = await db.scalar(select(CountryModel).where(CountryModel.code == movie.country))
        if not existing_country:
            existing_country = CountryModel(code=movie.country, name=None)
        db.add(existing_country)
        await db.flush()

        genres = []
        for genre in movie.genres:
            existing_genre = await db.scalar(
                select(GenreModel).where(GenreModel.name == genre))
            if not existing_genre:
                existing_genre = GenreModel(name=genre)
                db.add(existing_genre)
                await db.flush()
            genres.append(existing_genre)

        actors = []
        for actor in movie.actors:
            existing_actor = await db.scalar(
                select(ActorModel).where(ActorModel.name == actor))
            if not existing_actor:
                existing_actor = ActorModel(name=actor)
                db.add(existing_actor)
            actors.append(existing_actor)

        languages = []
        for language in movie.languages:
            existing_language = await db.scalar(
                select(LanguageModel).where(LanguageModel.name == language))
            if not existing_language:
                existing_language = LanguageModel(name=language)
                db.add(existing_language)
            languages.append(existing_language)

        new_movie = MovieModel(
            name=movie.name,
            date=movie.date,
            score=movie.score,
            overview=movie.overview,
            status=movie.status,
            budget=movie.budget,
            revenue=movie.revenue,
            country=existing_country,
            genres=genres,
            actors=actors,
            languages=languages,

        )
        db.add(new_movie)
        await db.commit()
        await db.refresh(new_movie, ["genres", "actors", "languages"])
        return MovieDetailSchema.model_validate(new_movie)

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.get('/movies/{movie_id}/', response_model=MovieDetailSchema)
async def get_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = await db.scalar((select(MovieModel)
                            .options(selectinload(MovieModel.genres),
                                     selectinload(MovieModel.actors),
                                     selectinload(MovieModel.languages),
                                     selectinload(MovieModel.country), )
                            .where(MovieModel.id == movie_id)))
    if not stmt:
        raise HTTPException(status_code=404, detail='Movie with the given ID was not found.')

    return stmt


@router.delete('/movies/{movie_id}/', responses={
    204: {
        "description": "Movie deleted successfully."
    },
    404: {
        "example": {"detail": "Movie with the given ID was not found."}
    },
}, )
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = await db.scalar((select(MovieModel)).where(MovieModel.id == movie_id))
    if not stmt:
        raise HTTPException(status_code=404, detail='Movie with the given ID was not found.')

    await db.delete(stmt)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/movies/{movie_id}/", responses={
    200: {
        "detail": "Movie updated successfully."
    },
    404: {
        "detail": "Movie with the given ID was not found."
    },
    400: {
        "detail": "Invalid input data."
    }
})
async def update_movie(movie_id: int, movie_atts: MovieUpdateSchema, db: AsyncSession = Depends(get_db)):
    movie = await db.scalar(select(MovieModel).where(MovieModel.id == movie_id))
    if not movie:
        raise HTTPException(status_code=404, detail='Movie with the given ID was not found.')

    for key, value in movie_atts.model_dump(exclude_unset=True).items():
        setattr(movie, key, value)

    try:
        await db.commit()
        await db.refresh(movie)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail='Invalid input data.')

    return {"detail": "Movie updated successfully."}
