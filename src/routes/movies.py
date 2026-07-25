from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import (
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
)
from schemas.movies import (
    MovieListResponseSchema,
    MovieDetailSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
    MessageResponseSchema,
)

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get(
    "/",
    response_model=MovieListResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    count_stmt = select(func.count(MovieModel.id))
    count_result = await db.execute(count_stmt)
    total_items = count_result.scalar_one()

    if total_items == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found.",
        )

    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found.",
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

    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}"
        if page > 1
        else None
    )
    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post(
    "/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
    movie_in: MovieCreateSchema,
    db: AsyncSession = Depends(get_db),
):
    dup_stmt = select(MovieModel).where(
        MovieModel.name == movie_in.name,
        MovieModel.date == movie_in.date,
    )
    dup_result = await db.execute(dup_stmt)
    if dup_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{movie_in.name}' and release "
                f"date '{movie_in.date}' already exists."
            ),
        )

    country_stmt = select(CountryModel).where(
        CountryModel.code == movie_in.country
    )
    country_result = await db.execute(country_stmt)
    country = country_result.scalars().first()
    if not country:
        country = CountryModel(code=movie_in.country, name=None)
        db.add(country)
        await db.flush()

    genres = []
    for g_name in movie_in.genres:
        g_stmt = select(GenreModel).where(GenreModel.name == g_name)
        g_res = await db.execute(g_stmt)
        genre = g_res.scalars().first()
        if not genre:
            genre = GenreModel(name=g_name)
            db.add(genre)
            await db.flush()
        genres.append(genre)

    actors = []
    for a_name in movie_in.actors:
        a_stmt = select(ActorModel).where(ActorModel.name == a_name)
        a_res = await db.execute(a_stmt)
        actor = a_res.scalars().first()
        if not actor:
            actor = ActorModel(name=a_name)
            db.add(actor)
            await db.flush()
        actors.append(actor)

    languages = []
    for l_name in movie_in.languages:
        l_stmt = select(LanguageModel).where(LanguageModel.name == l_name)
        l_res = await db.execute(l_stmt)
        language = l_res.scalars().first()
        if not language:
            language = LanguageModel(name=l_name)
            db.add(language)
            await db.flush()
        languages.append(language)

    new_movie = MovieModel(
        name=movie_in.name,
        date=movie_in.date,
        score=movie_in.score,
        overview=movie_in.overview,
        status=movie_in.status,
        budget=movie_in.budget,
        revenue=movie_in.revenue,
        country_id=country.id,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    db.add(new_movie)
    await db.commit()

    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == new_movie.id)
    )
    result = await db.execute(stmt)
    created_movie = result.scalars().first()

    return created_movie


@router.get(
    "/{movie_id}/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_200_OK,
)
async def get_movie_details(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    return movie


@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    await db.delete(movie)
    await db.commit()
    return None


@router.patch(
    "/{movie_id}/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def update_movie(
    movie_id: int,
    movie_in: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    update_data = movie_in.model_dump(exclude_unset=True)
    if not update_data:
        return {"detail": "Movie updated successfully."}

    for key, value in update_data.items():
        setattr(movie, key, value)

    await db.commit()

    return {"detail": "Movie updated successfully."}
