from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.crud import (
    get_list_movies_with_pagination_and_count,
    create_new_movie,
    get_or_create_default_objects,
    get_or_create_country,
    get_movie_by_id,
    delete_movie_by_id,
    update_movie_by_id,
)
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel

from schemas.movies import (
    MovieListResponseSchema,
    MovieListItemSchema,
    MovieDetailRequestSchema,
    MovieDetailResponseSchema,
    MoviePatchSchema,
)

router = APIRouter()
Database = Annotated[AsyncSession, Depends(get_db)]
Page = Annotated[int, Query(ge=1)]
PerPage = Annotated[int, Query(ge=1, le=20)]
MovieNotFound = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Movie with the given ID was not found.",
)


@router.get("/", response_model=MovieListResponseSchema)
async def get_movies_with_pagination(
    request: Request, db: Database, page: Page = 1, per_page: PerPage = 10
):
    rows = MovieListItemSchema.model_fields.keys()
    offset = (page - 1) * per_page
    limit = per_page
    base_path = request.url.path.replace("/api/v1", "")

    movies, counts = await get_list_movies_with_pagination_and_count(
        db=db, offset=offset, limit=limit, rows=rows
    )
    if movies:
        return {
            "movies": movies,
            "prev_page": (
                f"{base_path}?page={page - 1}&per_page={per_page}" if page > 1 else None
            ),
            "next_page": (
                f"{base_path}?page={page + 1}&per_page={per_page}"
                if page < (pages := (counts + per_page - 1) // per_page)
                else None
            ),
            "total_items": counts,
            "total_pages": pages,
        }
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="No movies found."
    )


@router.post(
    "/", response_model=MovieDetailResponseSchema, status_code=status.HTTP_201_CREATED
)
async def create_movie(db: Database, movie: MovieDetailRequestSchema):
    relation_fields = (
        (GenreModel, "name", "genres"),
        (ActorModel, "name", "actors"),
        (LanguageModel, "name", "languages"),
    )
    relation_objects_dict = dict()
    for model, field, attr_name in relation_fields:
        values = getattr(movie, attr_name)
        relation_object = await get_or_create_default_objects(
            db=db, model=model, field_to_search=field, filter_in=values
        )
        if relation_object:
            relation_objects_dict[attr_name] = relation_object
        else:
            ...
    relation_objects_dict["country"] = await get_or_create_country(
        db=db, country_code=movie.country
    )
    try:
        result = await create_new_movie(db=db, movie=movie, **relation_objects_dict)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
        )
    else:
        return result


@router.get("/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie(db: Database, movie_id: int):
    if movie_id < 1 or not (movie := await get_movie_by_id(db=db, movie_id=movie_id)):
        raise MovieNotFound
    return movie


@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(db: Database, movie_id: int):
    """
    The task did not say to delete related items.
    """
    if movie_id < 1 or not await delete_movie_by_id(db=db, movie_id=movie_id):
        raise MovieNotFound


@router.patch("/{movie_id}/")
async def update_movie(db: Database, movie_id: int, movie: MoviePatchSchema):
    if movie_id < 1 or not await update_movie_by_id(
        db=db, movie_id=movie_id, movie=movie
    ):
        raise MovieNotFound
    return {"detail": "Movie updated successfully."}
