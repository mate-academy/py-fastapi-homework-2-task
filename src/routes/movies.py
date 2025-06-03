from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from pydantic import ValidationError
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from database.models import (
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel
)
from database import get_db
from src.schemas.movies import (
    MovieCreateSchema,
    MovieDetailResponseSchema,
    MovieUpdate,
    MovieListResponseSchema
)


router = APIRouter()


def _build_pagination_url(request: Request, page: int, per_page: int) -> str:
    full_path_with_prefix = str(request.url.path)
    path_without_api_prefix = full_path_with_prefix.replace("/api/v1", "", 1)

    return f"{path_without_api_prefix}?page={page}&per_page={per_page}"


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a paginated list of movies",
    description="Fetches movies sorted by ID in descending order, with pagination links."
)
async def get_movies_list(
        request: Request,
        db: AsyncSession = Depends(get_db),
        page: int = Query(1, ge=1, description="Page number to retrieve"),
        per_page: int = Query(10, ge=1, le=20, description="Number of items per page (1-20)"),
) -> MovieListResponseSchema:
    """
    Retrieves a paginated list of movies from the database.
    Movies are sorted in descending order by their ID.
    """
    offset = (page - 1) * per_page

    total_items_query = select(func.count(MovieModel.id))
    total_items_result = await db.execute(total_items_query)
    total_items = total_items_result.scalar_one()

    total_items = total_items if total_items is not None else 0

    total_pages = (total_items + per_page - 1) // per_page if total_items > 0 else 0

    movies_query = select(MovieModel).options(
        joinedload(MovieModel.country),
        joinedload(MovieModel.genres),
        joinedload(MovieModel.actors),
        joinedload(MovieModel.languages)
    ).order_by(MovieModel.id.desc()).offset(offset).limit(per_page)

    movies_result = await db.execute(movies_query)
    movies_orm_objects = movies_result.scalars().unique().all()

    if not movies_orm_objects and (page > 1 or total_items == 0):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")

    prev_page_url = None
    if page > 1:
        prev_page_url = _build_pagination_url(request, page - 1, per_page)

    next_page_url = None
    if page < total_pages:
        next_page_url = _build_pagination_url(request, page + 1, per_page)

    return MovieListResponseSchema(
        movies=movies_orm_objects,
        prev_page=prev_page_url,
        next_page=next_page_url,
        total_pages=total_pages,
        total_items=total_items
    )


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Retrieve movie details by ID",
    description="Fetches detailed information about a specific movie, including related entities."
)
async def get_movie_details(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
) -> MovieDetailResponseSchema:
    movie_query = select(MovieModel).options(
        joinedload(MovieModel.country),
        joinedload(MovieModel.genres),
        joinedload(MovieModel.actors),
        joinedload(MovieModel.languages)
    ).where(MovieModel.id == movie_id)

    movie_result = await db.execute(movie_query)
    movie = movie_result.scalars().unique().one_or_none()

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    return movie


@router.post("/movies/", status_code=status.HTTP_201_CREATED)
async def create_movie(
        movie_data: MovieCreateSchema,
        db: AsyncSession = Depends(get_db)
) -> MovieDetailResponseSchema:
    existing_movie = await db.scalar(
        select(MovieModel)
        .where(MovieModel.name == movie_data.name)
        .where(MovieModel.date == movie_data.date)
    )
    if existing_movie:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists.",
        )
    try:
        country = await db.scalar(select(CountryModel).where(CountryModel.code == movie_data.country))
        if not country:
            country = CountryModel(code=movie_data.country)
            db.add(country)
            await db.flush()
        genres = []
        for genre_name in movie_data.genres:
            genre = await db.scalar(select(GenreModel).where(GenreModel.name == genre_name))
            if not genre:
                genre = GenreModel(name=genre_name)
                db.add(genre)
                await db.flush()
            genres.append(genre)
        actors = []
        for actor_name in movie_data.actors:
            actor = await db.scalar(select(ActorModel).where(ActorModel.name == actor_name))
            if not actor:
                actor = ActorModel(name=actor_name)
                db.add(actor)
                await db.flush()
            actors.append(actor)
        languages = []
        for language_name in movie_data.languages:
            language = await db.scalar(select(LanguageModel).where(LanguageModel.name == language_name))
            if not language:
                language = LanguageModel(name=language_name)
                db.add(language)
                await db.flush()
            languages.append(language)
        movie = MovieModel(
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
            languages=languages,
        )
        db.add(movie)
        await db.commit()
        return movie
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The input data is invalid (e.g., missing required fields, invalid values)"
        )


@router.delete(
    "/movies/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a movie by ID",
    response_description="No content on successful deletion"
)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):
    movie_query = select(MovieModel).filter(MovieModel.id == movie_id)
    result = await db.execute(movie_query)
    movie_to_delete = result.scalar_one_or_none()

    if movie_to_delete is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    await db.delete(movie_to_delete)
    await db.commit()

    return


@router.patch(
    "/movies/{movie_id}/",
    status_code=status.HTTP_200_OK,
    summary="Update a movie by ID",
    response_model=dict,
    responses={
        200: {"description": "Movie updated successfully."},
        404: {"description": "Movie not found."},
        400: {"description": "Invalid input data."}
    }
)
async def update_movie(
    movie_id: int,
    movie_update: MovieUpdate,
    db: AsyncSession = Depends(get_db)
):
    movie_query = select(MovieModel).filter(MovieModel.id == movie_id)
    result = await db.execute(movie_query)
    movie_to_update = result.scalar_one_or_none()

    if movie_to_update is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    try:
        update_data = movie_update.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(movie_to_update, key, value)

        await db.commit()
        await db.refresh(movie_to_update)

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input data: {e.errors()}"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input data. Error: {e}"
        )

    return {"detail": "Movie updated successfully."}
