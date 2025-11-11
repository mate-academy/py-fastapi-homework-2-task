from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieListResponseSchema,
    MovieListItemSchema,
    MovieDetailSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
)

router = APIRouter()


@router.get(
    "/movies/", response_model=MovieListResponseSchema,
    status_code=status.HTTP_200_OK)
async def get_movies_list(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db),
):
    total_items = (await db.execute(select(func.count(MovieModel.id)))).scalar() or 0
    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page
    offset = (page - 1) * per_page
    if offset >= total_items:
        raise HTTPException(status_code=404, detail="No movies found.")

    result = await db.execute(
        select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page)
    )
    movies = result.scalars().all()

    base_url = "/theater/movies/"
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return MovieListResponseSchema(
        movies=[MovieListItemSchema.model_validate(m) for m in movies],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)):
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
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found.")

    return MovieDetailSchema(
        id=movie.id,
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country={
            "id": movie.country.id,
            "code": movie.country.code,
            "name": movie.country.name,
        } if movie.country else None,
        genres=[{"id": g.id, "name": g.name} for g in movie.genres],
        actors=[{"id": a.id, "name": a.name} for a in movie.actors],
        languages=[
            {"id": language.id, "name": language.name}
            for language in movie.languages],

    )


@router.post(
    "/movies/", response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED)
async def create_movie(
        movie_data: MovieCreateSchema, db: AsyncSession = Depends(get_db)):

    existing = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie_data.name,
            MovieModel.date == movie_data.date,
        )
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data.name}' "
                   f"and release date '{movie_data.date}' already exists.",
        )

    new_movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
    )

    country = await db.scalar(select(CountryModel).where(CountryModel.code == movie_data.country))
    if not country:
        country = CountryModel(code=movie_data.country, name=movie_data.country)
        db.add(country)
        await db.flush()
    new_movie.country = country

    genres = []
    for g in movie_data.genres:
        genre = await db.scalar(select(GenreModel).where(GenreModel.name == g))
        if not genre:
            genre = GenreModel(name=g)
            db.add(genre)
            await db.flush()
        genres.append(genre)
    new_movie.genres = genres

    actors = []
    for a in movie_data.actors:
        actor = await db.scalar(select(ActorModel).where(ActorModel.name == a))
        if not actor:
            actor = ActorModel(name=a)
            db.add(actor)
            await db.flush()
        actors.append(actor)
    new_movie.actors = actors

    languages = []
    for language in movie_data.languages:
        lang = await db.scalar(
            select(LanguageModel).where(LanguageModel.name == language))
        if not lang:
            lang = LanguageModel(name=language)
            db.add(lang)
            await db.flush()
        languages.append(lang)
    new_movie.languages = languages

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)
    return await get_movie_by_id(new_movie.id, db)


@router.patch("/movies/{movie_id}/", status_code=status.HTTP_200_OK)
async def update_movie(
        movie_id: int, data: MovieUpdateSchema, db: AsyncSession = Depends(get_db)):

    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found.")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(movie, key, value)

    await db.commit()
    return {"detail": "Movie updated successfully."}


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):

    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()
    return None
