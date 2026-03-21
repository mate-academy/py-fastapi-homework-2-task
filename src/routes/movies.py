from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError

from database import get_db
from database.models import (
    MovieModel,
    GenreModel,
    ActorModel,
    CountryModel,
    LanguageModel,
)
from schemas.movies import (
    MovieCreateSchema,
    MovieUpdateSchema,
    MovieDetailSchema,
    MovieListResponseSchema,
)

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page
    count_res = await db.execute(select(func.count(MovieModel.id)))
    total_items = count_res.scalar()

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    stmt = (
        select(MovieModel).order_by(desc(MovieModel.id)).offset(offset).limit(per_page)
    )
    result = await db.execute(stmt)
    movies_list = result.scalars().all()

    if not movies_list:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page
    base_url = "/theater/movies/"

    return {
        "movies": movies_list,
        "prev_page": (
            f"{base_url}?page={page-1}&per_page={per_page}" if page > 1 else None
        ),
        "next_page": (
            f"{base_url}?page={page+1}&per_page={per_page}"
            if page < total_pages
            else None
        ),
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post("/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(data: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    check = await db.execute(
        select(MovieModel).filter_by(name=data.name, date=data.date)
    )
    if check.scalar():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{data.name}' and release date '{data.date}' already exists.",
        )

    country_stmt = await db.execute(select(CountryModel).filter_by(code=data.country))
    country = country_stmt.scalar_one_or_none()
    if not country:
        country = CountryModel(code=data.country)
        db.add(country)

    new_movie = MovieModel(
        name=data.name,
        date=data.date,
        score=data.score,
        overview=data.overview,
        status=data.status,
        budget=data.budget,
        revenue=data.revenue,
        country=country,
    )

    async def get_or_create_objs(model, names):
        if not names:
            return []
        res = await db.execute(select(model).filter(model.name.in_(names)))
        existing_objs = res.scalars().all()
        existing_names = {obj.name: obj for obj in existing_objs}
        objs = []
        for name in names:
            if name in existing_names:
                objs.append(existing_names[name])
            else:
                new_obj = model(name=name)
                db.add(new_obj)
                objs.append(new_obj)
        return objs

    new_movie.genres = await get_or_create_objs(GenreModel, data.genres)
    new_movie.actors = await get_or_create_objs(ActorModel, data.actors)
    new_movie.languages = await get_or_create_objs(LanguageModel, data.languages)

    db.add(new_movie)
    await db.commit()

    final_stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
            joinedload(MovieModel.country),
        )
        .filter(MovieModel.id == new_movie.id)
    )
    result = await db.execute(final_stmt)
    return result.unique().scalar_one()


@router.get("/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_detail(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
            joinedload(MovieModel.country),
        )
        .filter(MovieModel.id == movie_id)
    )
    result = await db.execute(stmt)
    movie = result.unique().scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


@router.delete("/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    await db.delete(movie)
    await db.commit()
    return None


@router.patch("/{movie_id}/")
async def update_movie(
    movie_id: int, request: Request, db: AsyncSession = Depends(get_db)
):
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    try:
        payload_data = await request.json()
        payload = MovieUpdateSchema(**payload_data)
    except ValidationError:
        raise HTTPException(status_code=400, detail="Invalid input data.")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(movie, key, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}
