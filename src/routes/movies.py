from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import (
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel
)
from schemas.movies import (
    MovieListResponseSchema,
    MovieDetailSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
)


router = APIRouter()


@router.get('/movies/', response_model=MovieListResponseSchema)
async def list_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    count_stmt = select(func.count(MovieModel.id))
    count_result = await db.execute(count_stmt)
    total_items = count_result.scalar_one()

    if total_items == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='No movies found.'
        )

    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='No movies found.'
        )

    offset = (page - 1) * per_page

    stmt = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    movies = result.scalars().all()

    prev_page = None
    next_page = None

    if page > 1:
        prev_page = f'/theater/movies/?page={page - 1}&per_page={per_page}'

    if page < total_pages:
        next_page = f'/theater/movies/?page={page + 1}&per_page={per_page}'

    response = {
        'movies': [
            {
                'id': movie.id,
                'name': movie.name,
                'date': movie.date,
                'score': movie.score,
                'overview': movie.overview
            }
            for movie in movies
        ],
        'prev_page': prev_page,
        'next_page': next_page,
        'total_pages': total_pages,
        'total_items': total_items
    }

    return response


@router.post('/movies/', response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(
    movie_data: MovieCreateSchema,
    db: AsyncSession = Depends(get_db)
):
    max_future_date = date.today() + timedelta(days=365)
    if movie_data.date > max_future_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid input data.'
        )

    existing_movie_stmt = select(MovieModel).where(
        (MovieModel.name == movie_data.name)
        & (MovieModel.date == movie_data.date)
    )
    existing_result = await db.execute(existing_movie_stmt)
    if existing_result.scalars().first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{movie_data.name}' and "
                f"release date '{movie_data.date}' already exists."
            )
        )

    try:
        country_stmt = select(CountryModel).where(
            CountryModel.code == movie_data.country
        )
        country_result = await db.execute(country_stmt)
        country = country_result.scalars().first()

        if not country:
            country = CountryModel(code=movie_data.country)
            db.add(country)
            await db.flush()

        genres = []
        for genre_name in movie_data.genres:
            genre_stmt = select(GenreModel).where(
                GenreModel.name == genre_name
            )
            genre_result = await db.execute(genre_stmt)
            genre = genre_result.scalars().first()

            if not genre:
                genre = GenreModel(name=genre_name)
                db.add(genre)
                await db.flush()

            genres.append(genre)

        actors = []
        for actor_name in movie_data.actors:
            actor_stmt = select(ActorModel).where(
                ActorModel.name == actor_name
            )
            actor_result = await db.execute(actor_stmt)
            actor = actor_result.scalars().first()

            if not actor:
                actor = ActorModel(name=actor_name)
                db.add(actor)
                await db.flush()

            actors.append(actor)

        languages = []
        for language_name in movie_data.languages:
            language_stmt = select(LanguageModel).where(
                LanguageModel.name == language_name
            )
            language_result = await db.execute(language_stmt)
            language = language_result.scalars().first()

            if not language:
                language = LanguageModel(name=language_name)
                db.add(language)
                await db.flush()

            languages.append(language)

        movie = MovieModel(
            name=movie_data.name,
            date=movie_data.date,
            score=movie_data.score,
            overview=movie_data.overview,
            status=movie_data.status,
            budget=movie_data.budget,
            revenue=movie_data.revenue,
            country_id=country.id,
            genres=genres,
            actors=actors,
            languages=languages
        )

        db.add(movie)
        await db.commit()
        await db.refresh(movie)

        await db.refresh(movie, ['country', 'genres', 'actors', 'languages'])

        return {
            'id': movie.id,
            'name': movie.name,
            'date': movie.date,
            'score': movie.score,
            'overview': movie.overview,
            'status': movie.status.value,
            'budget': float(movie.budget),
            'revenue': float(movie.revenue),
            'country': {
                'id': movie.country.id,
                'code': movie.country.code,
                'name': movie.country.name
            },
            'genres': [
                {'id': genre.id, 'name': genre.name}
                for genre in movie.genres
            ],
            'actors': [
                {'id': actor.id, 'name': actor.name}
                for actor in movie.actors
            ],
            'languages': [
                {'id': language.id, 'name': language.name}
                for language in movie.languages
            ]
        }

    except HTTPException:
        raise
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{movie_data.name}' and "
                f"release date '{movie_data.date}' already exists."
            )
        )
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid input data.'
        )


@router.get('/movies/{movie_id}/', response_model=MovieDetailSchema)
async def get_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )
    result = await db.execute(stmt)
    movie = result.unique().scalars().first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Movie with the given ID was not found.'
        )

    return {
        'id': movie.id,
        'name': movie.name,
        'date': movie.date,
        'score': movie.score,
        'overview': movie.overview,
        'status': movie.status.value,
        'budget': float(movie.budget),
        'revenue': float(movie.revenue),
        'country': {
            'id': movie.country.id,
            'code': movie.country.code,
            'name': movie.country.name
        },
        'genres': [
            {'id': genre.id, 'name': genre.name}
            for genre in movie.genres
        ],
        'actors': [
            {'id': actor.id, 'name': actor.name}
            for actor in movie.actors
        ],
        'languages': [
            {'id': language.id, 'name': language.name}
            for language in movie.languages
        ]
    }


@router.delete('/movies/{movie_id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Movie with the given ID was not found.'
        )

    await db.delete(movie)
    await db.commit()


@router.patch('/movies/{movie_id}/')
async def update_movie(
    movie_id: int,
    update_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Movie with the given ID was not found.'
        )

    try:
        if update_data.name is not None:
            movie.name = update_data.name

        if update_data.date is not None:
            movie.date = update_data.date

        if update_data.score is not None:
            movie.score = update_data.score

        if update_data.overview is not None:
            movie.overview = update_data.overview

        if update_data.status is not None:
            movie.status = update_data.status

        if update_data.budget is not None:
            movie.budget = update_data.budget

        if update_data.revenue is not None:
            movie.revenue = update_data.revenue

        await db.commit()

        return {'detail': 'Movie updated successfully.'}

    except HTTPException:
        raise
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid input data.'
        )
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid input data.'
        )
