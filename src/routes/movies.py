from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import MovieListResponseSchema, MovieDetailSchema
from schemas.movies import MovieCreateSchema, MovieUpdateSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
):
    total_items = await db.scalar(select(func.count()).select_from(MovieModel))

    if not total_items:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page
    if page > total_pages:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )

    offset = (page - 1) * per_page
    movies = await db.scalars(
        select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(
            per_page
        )
    )
    movies_list = movies.all()

    BASE_URL = "/theater/movies/"
    prev_page = f"{BASE_URL}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{BASE_URL}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": movies_list,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy.orm import selectinload

    # can be loaded by lazy="selectin" or lazy='joined' in models
    movie = (await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages)
        )
        .filter(MovieModel.id == movie_id)
    )).scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    return MovieDetailSchema.model_validate(movie)


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED
)
async def create_movie(
        movie: MovieCreateSchema,
        db: AsyncSession = Depends(get_db)
):
    existing_movie = (await db.execute(
        select(MovieModel).filter(
            MovieModel.name == movie.name,
            MovieModel.date == movie.date
        )
    )).scalar_one_or_none()

    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    try:
        country = (await db.execute(
            select(CountryModel).filter(CountryModel.code == movie.country)
        )).scalar_one_or_none()
        if not country:
            country = CountryModel(
                code=movie.country,
                name=movie.country
            )
            db.add(country)
            await db.flush()

        genres = []
        for genre_name in movie.genres:
            genre = (await db.execute(
                select(GenreModel).filter(GenreModel.name == genre_name)
            )).scalar_one_or_none()
            if not genre:
                genre = GenreModel(name=genre_name)
                db.add(genre)
                await db.flush()
            genres.append(genre)

        actors = []
        for actor_name in movie.actors:
            actor = (await db.execute(
                select(ActorModel).filter(ActorModel.name == actor_name)
            )).scalar_one_or_none()
            if not actor:
                actor = ActorModel(name=actor_name)
                db.add(actor)
                await db.flush()
            actors.append(actor)

        languages = []
        for language_name in movie.languages:
            language = (await db.execute(
                select(LanguageModel).filter(
                    LanguageModel.name == language_name
                )
            )).scalar_one_or_none()
            if not language:
                language = LanguageModel(name=language_name)
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
            languages=languages
        )
        db.add(new_movie)

        await db.commit()

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Failed to create movie due to integrity error. Please check the data."
        )

    return MovieDetailSchema.model_validate(new_movie)


@router.delete(
    "/movies/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    movie = (await db.execute(
        select(MovieModel).filter(MovieModel.id == movie_id)
    )).scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()
    return


@router.patch("/movies/{movie_id}/", status_code=status.HTTP_200_OK)
async def update_movie(
        movie_id: int,
        movie_update: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db)
):
    movie = (await db.execute(
        select(MovieModel).filter(MovieModel.id == movie_id)
    )).scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    update_data = movie_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(movie, key, value)

    await db.commit()
    await db.refresh(movie)

    return {"detail": "Movie updated successfully."}
