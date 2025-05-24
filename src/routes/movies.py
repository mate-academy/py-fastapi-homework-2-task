from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


from database import get_db, MovieModel
from schemas import (
    MovieCreateSchema,
    MovieDetailSchema,
    MovieListResponseSchema,
    MoviePartialUpdateSchema,
    MoviePartialUpdateSuccessSchema
)
from crud import (
    get_movie_list,
    generate_pagination_links,
    create_movie,
    get_single_movie,
    partial_update_movie
)

router = APIRouter()


async def common_parameters(
    movie_id: int,
    db_session: AsyncSession = Depends(get_db)
):
    return {"movie_id": movie_id, "db_session": db_session}


CommonsDep = Annotated[dict, Depends(common_parameters)]


@router.get("/movies/", response_model=MovieListResponseSchema)
async def read_movies(
    db_session: AsyncSession = Depends(get_db),
    page: int = Query(
        default=1,
        ge=1,
        description="Specifies the page number to retrieve."
    ),
    per_page: int = Query(
        default=10,
        ge=1,
        le=20,
        description="Specifies the number of items to display per page."
    )
):

    movies = await get_movie_list(db=db_session, page=page, per_page=per_page)

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_items = await db_session.scalar(
        select(func.count()).select_from(MovieModel)
    )
    total_pages = (total_items + per_page - 1) // per_page

    pagination_links = generate_pagination_links(
        total_pages=total_pages,
        page=page,
        per_page=per_page
    )

    return {
        "movies": movies,
        "prev_page": pagination_links["prev_page"],
        "next_page": pagination_links["next_page"],
        "total_pages": total_pages,
        "total_items": total_items
    }


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def add_movie(
    movie: MovieCreateSchema,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Create a new movie with all related objects.
    Returns the created movie with all relationships.
    """
    try:
        new_movie = await create_movie(
            db=db_session,
            movie=movie
        )
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date "
            f"'{movie.date}' already exists."
        )
    return new_movie


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def read_single_movie(commons: CommonsDep):
    """
    Retrieve detailed information about a specific movie and its related
    objects by its unique ID.
    """

    movie = await get_single_movie(
        db=commons["db_session"],
        movie_id=commons["movie_id"]
    )

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(commons: CommonsDep):
    """
    Deletes a specific movie by its unique ID. If the movie with the specified
    ID does not exist, a 404 Not Found error is raised.
    """

    movie = await commons["db_session"].get(
        entity=MovieModel,
        ident=commons["movie_id"]
    )

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    await commons["db_session"].delete(movie)
    await commons["db_session"].commit()


@router.patch(
    "/movies/{movie_id}/",
    response_model=MoviePartialUpdateSuccessSchema
)
async def update_movie_partial(
    commons: CommonsDep,
    movie: MoviePartialUpdateSchema
):
    """
    Partially updates a movie with the given ID.
    Returns a success message, or a 404 Not Found error if the movie
    with the given ID does not exist.
    """
    movie = await partial_update_movie(
        db=commons["db_session"],
        movie_id=commons["movie_id"],
        movie=movie
    )

    return MoviePartialUpdateSuccessSchema(
        detail="Movie updated successfully."
    )
