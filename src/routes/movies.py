from fastapi import APIRouter, HTTPException, Query, Response
from starlette import status

import crud
import schemas
from database.dependencies import DBDep

router = APIRouter()


@router.get(
    "/movies/",
    response_model=schemas.MovieListResponseSchema
)
async def read_movies(
    db: DBDep,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20)
):
    movies, total_items, total_pages = await crud.get_all_movies(
        db=db,
        page=page,
        per_page=per_page
    )

    if total_items == 0:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )

    if page > total_pages:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )

    base_path = "/theater/movies/"

    return {
        "movies": movies,
        "prev_page": f"{base_path}"
                     f"?page={page - 1}"
                     f"&per_page={per_page}" if page > 1 else None,
        "next_page": f"{base_path}"
                     f"?page={page + 1}"
                     f"&per_page={per_page}" if page < total_pages else None,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post(
    "/movies/",
    response_model=schemas.MovieCreateResponseSchema,
    status_code=status.HTTP_201_CREATED
)
async def create_movie(
    movie_data: schemas.MovieCreateRequestSchema,
    db: DBDep,
):
    return await crud.create_movie(db=db, movie_data=movie_data)


@router.get(
    "/movies/{movie_id}/",
    response_model=schemas.MovieCreateResponseSchema
)
async def read_single_movie(
    movie_id: int,
    db: DBDep,
):
    movie = await crud.get_movie_by_id(
        db=db,
        movie_id=movie_id
    )

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    return movie


@router.delete(
    "/movies/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_movie(
    movie_id: int,
    db: DBDep,
):
    movie = await crud.get_movie_by_id(
        db=db,
        movie_id=movie_id
    )
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    await crud.delete_movie(db=db, movie=movie)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/movies/{movie_id}/",
    status_code=status.HTTP_200_OK
)
async def update_movie(
    movie_update: schemas.MovieUpdateRequestSchema,
    movie_id: int,
    db: DBDep,
):
    movie = await crud.get_movie_by_id(
        db=db,
        movie_id=movie_id
    )
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    await crud.patch_movie_fields(
        db=db,
        movie=movie,
        movie_update=movie_update
    )

    return {"detail": "Movie updated successfully."}
