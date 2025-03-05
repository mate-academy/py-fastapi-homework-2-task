from fastapi import APIRouter, Depends, HTTPException, Query, status
from requests import Session
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from datetime import date, datetime
from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from src.schemas.movies import (MovieDetailSchema,
                                MovieUpdateRequestSchema,
                                MoviesListItemSchema,
                                MovieCreateRequestShema,
                                MovieUpdateRequestSchema,
                                MoviesListResponseSchema)


router = APIRouter()

@router.get("/movies", response_model=list[MoviesListResponseSchema])
async def get_movies(page: int = Query(1, ge=1),
                     db: AsyncSession = Depends(get_db),
                     per_page: int = Query(10, ge=1)):
    total_items_queri = await db.execute(select(func.count(MovieModel.id)))
    total_items = total_items_queri.scalar()
    
    total_pages = (total_items + per_page - 1) // per_page
    
    movies_query = (select(MovieModel).
                    order_by(MovieModel.id).
                    offset((page - 1) * per_page).
                    limit(per_page))
    movies_result = await db.execute(movies_query)
    db_movies = movies_result.scalars().all()
    
    if not db_movies:
        raise HTTPException(status_code=404, detail="No movies found")
    
    movies = [MoviesListItemSchema.from_orm(movie) for movie in db_movies]
    
    prev_page = (f"/movies?page={page - 1}&per_page={per_page}" if page > 1 else None)
    next_page = (f"/movies?page={page + 1}&per_page={per_page}"\
                if page < total_pages else None)
    return {"movies": movies,
            "prev_page": prev_page,
            "next_page": next_page,
            "total_pages": total_pages,
            "total_items": total_items}
    
@router.get("/movies/{movie_id}", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    queryset = (select(MovieModel).
                options(
                    joinedload(MovieModel.country),
                    joinedload(MovieModel.languages),
                    joinedload(MovieModel.actors),
                    joinedload(MovieModel.genres)
                ).where(MovieModel.id == movie_id)
                )
    result = await db.execute(queryset)
    movie = result.scalar_one_or_none()
    
    if not movie:
        raise HTTPException(status_code=404,
                            detail="Movie with the given ID was not found.")
    return MovieDetailSchema.from_orm(movie)

@router.post("/movies/", response_model=MovieCreateRequestShema)
async def create_movie(movie_data: MovieCreateRequestShema, db: Session = Depends(get_db)):
    movie = MovieModel(**movie_data.dict())
    db.add(movie)
    try:
        await db.commit()
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Invalid data provided.")
    return movie

@router.patch("/movies/{movie_id}/", response_model=MovieUpdateRequestSchema)
async def update_movie(
    movie_id: int, update_data: MovieUpdateRequestSchema, db: Session = Depends(get_db)
):
    query = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(query)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    update_dict = update_data.dict(exclude_unset=True)
    if "date" in update_dict and update_dict[
        "date"
    ] > date.today() + datetime.timedelta(days=365):
        raise HTTPException(
            status_code=400, detail="Date cannot be more than one year in the future."
        )

    for key, value in update_dict.items():
        setattr(movie, key, value)

    await db.commit()
    await db.refresh(movie)
    return {"detail": "Movie updated successfully."}

@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    query = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(query)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    db.delete(movie)
    await db.commit()
    return
