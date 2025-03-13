from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

import crud
from schemas.movies import MovieListResponseSchema, MovieCreate, MovieDetail

from database import get_db


router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(1, alias="page", ge=1),
    per_page: int = Query(10, alias="per_page", ge=1),
    db: AsyncSession = Depends(get_db),
):

    (return_movies, page, total_movies, total_pages) = await crud.get_movies(
        db=db, page=page, per_page=per_page
    )

    if not return_movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    base_url = "/theater/movies/"
    next_page = (
        f"{base_url}?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None

    if return_movies:
        return {
            "movies": return_movies,
            "total_items": total_movies,
            "total_pages": total_pages,
            "next_page": next_page,
            "prev_page": prev_page,
        }

    raise HTTPException(status_code=404, detail="No movies found.")


@router.get("/movies/{movie_id}/", response_model=MovieDetail)
async def retrieve_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await crud.retrieve_movie(db=db, movie_id=movie_id)
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


@router.post("/movies/", response_model=MovieDetail)
async def create_movie(movie: MovieCreate, db: AsyncSession = Depends(get_db)):
    new_movie = await crud.create_movie(db=db, movie=movie)
    new_movie = jsonable_encoder(new_movie)
    return JSONResponse(status_code=201, content=new_movie)


@router.patch("/movies/{movie_id}/")
async def update_movie(movie_id: int, movie: dict, db: AsyncSession = Depends(get_db)):
    movie = await crud.update_movie(db=db, movie_data=movie, movie_id=movie_id)
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    return JSONResponse(
        status_code=200, content={"detail": "Movie updated successfully."}
    )


@router.delete("/movies/{movie_id}/")
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await crud.delete_movie(db=db, movie_id=movie_id)
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return JSONResponse(status_code=204, content={})