from datetime import date, timedelta

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Body
)
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import (
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel, MovieStatusEnum
)
import math


router = APIRouter()

@router.get("/movies/")
async def get_movies(
    page: int = Query(1, ge=1, description="Page number (starting at 1)"),
    per_page: int = Query(10, ge=1, le=20, description="Number of items per page (1-20)"),
    db: AsyncSession = Depends(get_db)
):
    count_stmt = select(func.count()).select_from(MovieModel)
    count_result = await db.execute(count_stmt)
    total_items = count_result.scalar()
    total_pages = math.ceil(total_items / per_page) if total_items else 0

    if total_items == 0 or page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    offset = (page - 1) * per_page

    stmt = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    movies_list = result.scalars().all()

    if not movies_list:
        raise HTTPException(status_code=404, detail="No movies found.")

    movies = []
    for movie in movies_list:
        movies.append({
            "id": movie.id,
            "name": movie.name,
            "date": movie.date.strftime("%Y-%m-%d") if movie.date else None,
            "score": movie.score,
            "overview": movie.overview
        })

    prev_page = f"/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items
    }


@router.post("/movies/", status_code=201)
async def create_movie(
    movie_data: dict = Body(...),
    db: AsyncSession = Depends(get_db)
):
    required_fields = [
        "name", "date", "score", "overview", "status",
        "budget", "revenue", "country", "genres", "actors", "languages"
    ]
    for field in required_fields:
        if field not in movie_data:
            raise HTTPException(status_code=400, detail="Invalid input data.")

    if len(movie_data["name"]) > 255:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    try:
        release_date = date.fromisoformat(movie_data["date"])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid input data.")
    if release_date > date.today() + timedelta(days=365):
        raise HTTPException(status_code=400, detail="Invalid input data.")

    try:
        score = float(movie_data["score"])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid input data.")
    if not (0 <= score <= 100):
        raise HTTPException(status_code=400, detail="Invalid input data.")

    try:
        budget = float(movie_data["budget"])
        revenue = float(movie_data["revenue"])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid input data.")
    if budget < 0 or revenue < 0:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    allowed_status = [
        MovieStatusEnum.RELEASED.value,
        MovieStatusEnum.POST_PRODUCTION.value,
        MovieStatusEnum.IN_PRODUCTION.value
    ]
    if movie_data["status"] not in allowed_status:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    stmt = select(MovieModel).where(
        MovieModel.name == movie_data["name"],
        MovieModel.date == release_date
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data['name']}' and release date '{movie_data['date']}' already exists."
        )


    stmt = select(CountryModel).where(CountryModel.code == movie_data["country"])
    result = await db.execute(stmt)
    country_obj = result.scalar_one_or_none()
    if not country_obj:
        country_obj = CountryModel(code=movie_data["country"], name=None)
        db.add(country_obj)
        await db.flush()

    genre_objs = []
    for genre_name in set(movie_data["genres"]):
        stmt = select(GenreModel).where(GenreModel.name == genre_name)
        result = await db.execute(stmt)
        genre_obj = result.scalar_one_or_none()
        if not genre_obj:
            genre_obj = GenreModel(name=genre_name)
            db.add(genre_obj)
            await db.flush()
        genre_objs.append(genre_obj)

    actor_objs = []
    for actor_name in set(movie_data["actors"]):
        stmt = select(ActorModel).where(ActorModel.name == actor_name)
        result = await db.execute(stmt)
        actor_obj = result.scalar_one_or_none()
        if not actor_obj:
            actor_obj = ActorModel(name=actor_name)
            db.add(actor_obj)
            await db.flush()
        actor_objs.append(actor_obj)

    language_objs = []
    for language_name in set(movie_data["languages"]):
        stmt = select(LanguageModel).where(LanguageModel.name == language_name)
        result = await db.execute(stmt)
        language_obj = result.scalar_one_or_none()
        if not language_obj:
            language_obj = LanguageModel(name=language_name)
            db.add(language_obj)
            await db.flush()
        language_objs.append(language_obj)

    new_movie = MovieModel(
        name=movie_data["name"],
        date=release_date,
        score=score,
        overview=movie_data["overview"],
        status=movie_data["status"],
        budget=budget,
        revenue=revenue,
        country_id=country_obj.id
    )
    new_movie.country = country_obj
    new_movie.genres = genre_objs
    new_movie.actors = actor_objs
    new_movie.languages = language_objs

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    return {
        "id": new_movie.id,
        "name": new_movie.name,
        "date": new_movie.date.strftime("%Y-%m-%d"),
        "score": new_movie.score,
        "overview": new_movie.overview,
        "status": new_movie.status,
        "budget": float(new_movie.budget),
        "revenue": new_movie.revenue,
        "country": {
            "id": new_movie.country.id,
            "code": new_movie.country.code,
            "name": new_movie.country.name,
        },
        "genres": [{"id": genre.id, "name": genre.name} for genre in new_movie.genres],
        "actors": [{"id": actor.id, "name": actor.name} for actor in new_movie.actors],
        "languages": [{"id": language.id, "name": language.name} for language in new_movie.languages],
    }


@router.get("/movies/{movie_id}/")
async def get_movie_details(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages)
        )
        .where(MovieModel.id == movie_id)
    )
    result = await db.execute(stmt)
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    return {
        "id": movie.id,
        "name": movie.name,
        "date": movie.date.strftime("%Y-%m-%d") if movie.date else None,
        "score": movie.score,
        "overview": movie.overview,
        "status": movie.status,
        "budget": float(movie.budget),
        "revenue": movie.revenue,
        "country": {
            "id": movie.country.id,
            "code": movie.country.code,
            "name": movie.country.name,
        },
        "genres": [
            {"id": genre.id, "name": genre.name}
            for genre in movie.genres
        ],
        "actors": [
            {"id": actor.id, "name": actor.name}
            for actor in movie.actors
        ],
        "languages": [
            {"id": language.id, "name": language.name}
            for language in movie.languages
        ],
    }


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    await db.delete(movie)
    await db.commit()
    return


@router.patch("/movies/{movie_id}/")
async def update_movie(
    movie_id: int,
    movie_data: dict = Body(...),
    db: AsyncSession = Depends(get_db)
):
    allowed_fields = {"name", "date", "score", "overview", "status", "budget", "revenue"}
    for key in movie_data.keys():
        if key not in allowed_fields:
            raise HTTPException(status_code=400, detail="Invalid input data.")

    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    if "name" in movie_data:
        if len(movie_data["name"]) > 255:
            raise HTTPException(status_code=400, detail="Invalid input data.")
        movie.name = movie_data["name"]

    if "date" in movie_data:
        try:
            new_date = date.fromisoformat(movie_data["date"])
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid input data.")
        if new_date > date.today() + timedelta(days=365):
            raise HTTPException(status_code=400, detail="Invalid input data.")
        movie.date = new_date

    if "score" in movie_data:
        try:
            new_score = float(movie_data["score"])
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid input data.")
        if not (0 <= new_score <= 100):
            raise HTTPException(status_code=400, detail="Invalid input data.")
        movie.score = new_score

    if "overview" in movie_data:
        movie.overview = movie_data["overview"]

    if "status" in movie_data:
        allowed_status = [
            MovieStatusEnum.RELEASED.value,
            MovieStatusEnum.POST_PRODUCTION.value,
            MovieStatusEnum.IN_PRODUCTION.value
        ]
        if movie_data["status"] not in allowed_status:
            raise HTTPException(status_code=400, detail="Invalid input data.")
        movie.status = movie_data["status"]

    if "budget" in movie_data:
        try:
            new_budget = float(movie_data["budget"])
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid input data.")
        if new_budget < 0:
            raise HTTPException(status_code=400, detail="Invalid input data.")
        movie.budget = new_budget

    if "revenue" in movie_data:
        try:
            new_revenue = float(movie_data["revenue"])
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid input data.")
        if new_revenue < 0:
            raise HTTPException(status_code=400, detail="Invalid input data.")
        movie.revenue = new_revenue

    await db.commit()
    await db.refresh(movie)

    return {"detail": "Movie updated successfully."}

