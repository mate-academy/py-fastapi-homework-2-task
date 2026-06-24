import math
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from database import get_db
from database.models import (
    MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel
)
from schemas.movies import (
    MovieListResponse, MovieCreateRequest, MovieDetailResponse, MovieUpdateRequest
)

router = APIRouter(prefix="/movies", tags=["Movies"])


# --- Task 1: Movies List Endpoint ---
@router.get("/", response_model=MovieListResponse)
async def get_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
):
    total_items = await db.scalar(select(func.count()).select_from(MovieModel))

    if total_items == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)

    if page > total_pages:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")

    offset = (page - 1) * per_page

    query = select(MovieModel).order_by(desc(MovieModel.id)).limit(per_page).offset(offset)
    result = await db.execute(query)
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")

    prev_page_url = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page_url = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": movies,
        "prev_page": prev_page_url,
        "next_page": next_page_url,
        "total_pages": total_pages,
        "total_items": total_items
    }


# --- Task 2: Movie Creation Endpoint ---
@router.post("/", response_model=MovieDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_movie(movie_data: MovieCreateRequest, db: AsyncSession = Depends(get_db)):
    existing_movie = await db.execute(
        select(MovieModel).where(MovieModel.name == movie_data.name, MovieModel.date == movie_data.date)
    )
    if existing_movie.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists."
        )

    country_res = await db.execute(select(CountryModel).where(CountryModel.code == movie_data.country))
    country = country_res.scalars().first()
    if not country:
        country = CountryModel(code=movie_data.country, name=None)
        db.add(country)

    async def get_or_create(model, names_list):
        items = []
        for name in names_list:
            res = await db.execute(select(model).where(model.name == name))
            item = res.scalars().first()
            if not item:
                item = model(name=name)
                db.add(item)
            items.append(item)
        return items

    genres = await get_or_create(GenreModel, movie_data.genres)
    actors = await get_or_create(ActorModel, movie_data.actors)
    languages = await get_or_create(LanguageModel, movie_data.languages)

    new_movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages
    )

    db.add(new_movie)
    await db.commit()

    query = select(MovieModel).where(MovieModel.id == new_movie.id).options(
        selectinload(MovieModel.country),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.languages)
    )
    result = await db.execute(query)
    movie_with_relations = result.scalars().first()

    return movie_with_relations


# --- Task 3: Movie Details Endpoint ---
@router.get("/{movie_id}/", response_model=MovieDetailResponse)
async def get_movie_details(movie_id: int, db: AsyncSession = Depends(get_db)):
    query = select(MovieModel).where(MovieModel.id == movie_id).options(
        selectinload(MovieModel.country),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.languages)
    )
    result = await db.execute(query)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")

    return movie


# --- Task 4: Movie Deletion Endpoint ---
@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()

    return None


# --- Task 5: Movie Update Endpoint ---
@router.patch("/{movie_id}/")
async def update_movie(movie_id: int, update_data: MovieUpdateRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")

    update_dict = update_data.model_dump(exclude_unset=True)

    for key, value in update_dict.items():
        setattr(movie, key, value)

    await db.commit()

    return {"detail": "Movie updated successfully."}
