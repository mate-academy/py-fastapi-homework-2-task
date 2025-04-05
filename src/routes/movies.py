from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from starlette.responses import JSONResponse

from database import get_db, MovieModel
from database.models import (
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel
)
from schemas.movies import (
    MovieListResponseSchema,
    MoviePutRequest,
    CountryDetailResponse,
    GenreDetailResponse,
    ActorDetailResponse,
    LanguageDetailResponse,
    MoviePostResponseSchema
)

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        page: int = Query(1, ge=1, description="Page number (>=1)"),
        per_page: int = Query(10, ge=1, le=20, description="Number of movies per page (1-20)"),
        db: AsyncSession = Depends(get_db)
):
    total_count = await db.execute(select(MovieModel))
    total_items = len(total_count.scalars().all())

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages > 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    query = select(MovieModel).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    movies = result.scalars().all()

    prev_page = f"/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items
    }


@router.post("/movies/")
async def submit_score(
        movie: MoviePutRequest,
        db: AsyncSession = Depends(get_db)
) -> JSONResponse:

    existing_movie = await db.execute(select(MovieModel).
                                      filter_by(name=movie.name,
                                                date=movie.date)
                                      )
    if existing_movie.scalar():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and "
                   f"release date '{movie.date}' already exists."
        )

    result = await db.execute(select(CountryModel).where(CountryModel.code == movie.country))
    db_country = result.scalar_one_or_none()
    if db_country is None:
        # raise HTTPException(status_code=404, detail="Country not found")
        db_country = CountryModel(code=movie.country, name=movie.name)
        db.add(db_country)
        await db.commit()

    genres = []
    for genre in movie.genres:
        result = await db.execute(select(GenreModel).where(GenreModel.name == genre))
        db_genre = result.scalar_one_or_none()
        if db_genre is None:
            # raise HTTPException(status_code=404, detail="Genre not found")
            db_genre = GenreModel(name=genre)
            db.add(db_genre)
            await db.commit()
        genres.append(db_genre)

    actors = []
    for actor in movie.actors:
        result = await db.execute(select(ActorModel).where(ActorModel.name == actor))
        db_actor = result.scalar_one_or_none()
        if db_actor is None:
            # raise HTTPException(status_code=404, detail="Actor not found")
            db_actor = ActorModel(name=actor)
            db.add(db_actor)
            await db.commit()
        actors.append(db_actor)

    languages = []
    for language in movie.languages:
        result = await db.execute(select(LanguageModel).where(LanguageModel.name == language))
        db_language = result.scalar_one_or_none()
        if db_language is None:
            # raise HTTPException(status_code=404, detail="Language not found")
            db_language = LanguageModel(name=language)
            db.add(db_language)
            await db.commit()
        languages.append(db_language)

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country_id=db_country.id,
        country=db_country,
        genres=genres,
        actors=actors,
        languages=languages
    )
    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    movie_query = (
        select(MovieModel)
        .where(MovieModel.id == new_movie.id)
        .options(
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages)
        )
    )

    result = await db.execute(movie_query)
    new_movie = result.scalar_one_or_none()

    response_data = MoviePostResponseSchema(
            id=new_movie.id,
            name=new_movie.name,
            date=new_movie.date.isoformat(),
            score=new_movie.score,
            overview=new_movie.overview,
            status=new_movie.status,
            budget=new_movie.budget,
            revenue=new_movie.revenue,
            country_id=new_movie.country.id,
            country=CountryDetailResponse(
                id=new_movie.country.id,
                code=new_movie.country.code,
                name=new_movie.country.name
            ),
            genres=[GenreDetailResponse(id=genre.id, name=genre.name)
                    for genre in new_movie.genres],
            actors=[ActorDetailResponse(id=actor.id, name=actor.name)
                    for actor in new_movie.actors],
            languages=[LanguageDetailResponse(id=language.id, name=language.name)
                       for language in new_movie.languages]
        ).dict()

    return JSONResponse(
        content=response_data,
        status_code=201
    )
