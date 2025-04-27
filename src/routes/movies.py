from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette import status

from crud.movies import create_movie, delete_movie, update_movie, get_movie_by_id, get_movies
from database import get_db
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieListResponseSchema, MovieCreate, Movie, MovieUpdate, MovieDetailSchema

router = APIRouter()

# @router.get("/movies/", response_model=MovieListResponse)
# async def get_all_movies(
#         page: int = Query(1, ge=1),
#         per_page: int = Query(10, ge=1, le=20),
#         db: AsyncSession = Depends(get_db)
# ):
#     offset = (page - 1) * per_page
#     result = await db.execute(select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page))
#     movies = result.scalars().all()
#
#     if not movies:
#         raise HTTPException(status_code=404, detail="No movies found.")
#
#     total_items_result = await db.execute(select(MovieModel))
#     total_items = len(total_items_result.scalars().all())
#     total_pages = (total_items + per_page - 1) // per_page
#
#     prev_page = f"/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
#     next_page = f"/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None
#
#     return {
#         "movies": movies,
#         "prev_page": prev_page,
#         "next_page": next_page,
#         "total_pages": total_pages,
#         "total_items": total_items
#     }
#
#
# @router.get("/movies/{movie_id}/", response_model=Movie)
# async def get_movie_details(movie_id: int, db: AsyncSession = Depends(get_db)):
#     result = await db.execute(
#         select(MovieModel).options(
#             joinedload(MovieModel.country),
#             joinedload(MovieModel.genres),
#             joinedload(MovieModel.actors),
#             joinedload(MovieModel.languages),
#         )
#         .where(MovieModel.id == movie_id))
#     movie = result.scalars().first()
#
#     if not movie:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Movie with the given ID was not found."
#         )
#
#     return movie
#
#
# @router.post("/movies/", response_model=Movie, status_code=status.HTTP_201_CREATED)
# async def create_movie(movie_data: MovieCreate, db: AsyncSession = Depends(get_db)):
#     existing_movie = await db.execute(
#         select(MovieModel).where(
#             MovieModel.name == movie_data.name,
#             MovieModel.date == movie_data.data
#         )
#     )
#     if existing_movie.scalars().first():
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.data}' already exists."
#         )
#
#     country_result = await db.execute(select(CountryModel).where(CountryModel.code == movie_data.country))
#     country = country_result.scalars().first()
#
#     if not country:
#         country = CountryModel(code=movie_data.country)
#         db.add(country)
#         await db.flush()
#
#     genres = []
#     for genre_name in movie_data.genres:
#         genre_result = await db.execute(select(GenreModel).where(GenreModel.name == genre_name))
#         genre = genre_result.scalars().first()
#
#         if not genre:
#             genre = GenreModel(name=genre_name)
#             db.add(genre)
#             await db.flush()
#         genres.append(genre)
#
#     actors = []
#     for actor_name in movie_data.actors:
#         actor_result = await db.execute(select(ActorModel).where(ActorModel.name == actor_name))
#         actor = actor_result.scalars().first()
#
#         if not actor:
#             actor = ActorModel(name=actor_name)
#             db.add(actor)
#             await db.flush()
#         actors.append(actor)
#
#     languages = []
#     for lang_name in movie_data.languages:
#         lang_result = await db.execute(select(LanguageModel).where(LanguageModel.name == lang_name))
#         lang = lang_result.scalars().first()
#         if not lang:
#             lang = LanguageModel(name=lang_name)
#             db.add(lang)
#             await db.flush()
#         languages.append(lang)
#
#     movie = MovieModel(
#         name=movie_data.name,
#         date=movie_data.date,
#         score=movie_data.score,
#         overview=movie_data.overview,
#         status=movie_data.status,
#         budget=movie_data.budget,
#         revenue=movie_data.revenue,
#         country=country,
#         genres=genres,
#         actors=actors,
#         languages=languages
#     )
#
#     db.add(movie)
#     await db.commit()
#     await db.refresh(movie)
#
#     return movie
#
#
# @router.patch("/movies/{movie_id}/", response_model=MovieUpdate)
# async  def update_movie(movie_id: int, db: AsyncSession = Depends(get_db)):


@router.post("/movies/", response_model=Movie)
async def add_movie(movie: MovieCreate, db: AsyncSession = Depends(get_db)):
    new_movie = await create_movie(db, movie)
    return new_movie

@router.get("/movies/", response_model=MovieListResponseSchema)
async def list_movies(db: AsyncSession = Depends(get_db)):
    movies = await get_movies(db)
    return movies


@router.get("/movies/{movie_id}", response_model=MovieDetailSchema)
async def read_movies(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_movie_by_id(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie

@router.put("/movies/{movie_id}", response_model=Movie)
async def edit_movie(movie_id: int, movie: MovieUpdate,
db: AsyncSession = Depends(get_db)):
    updated_movie = await update_movie(db, movie_id, movie)
    if not updated_movie:
        raise HTTPException(status_code=404, detail="Film not found")
    return updated_movie

@router.delete("/movies/{movie_id}", response_model=Movie)
async def remove_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    deleted_movie = await delete_movie(db, movie_id)
    if not deleted_movie:
        raise HTTPException(status_code=404, detail="Film not found")
    return deleted_movie
