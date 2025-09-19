from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel, MovieStatusEnum
from schemas.movies import (
    MovieListResponseSchema, MovieListItemSchema, MovieDetailSchema,
    MovieCreateRequest, MovieUpdateRequest
)

router = APIRouter(prefix="/movies")


@router.get("/", response_model=MovieListResponseSchema)
async def get_movies(
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(10, ge=1, le=20, description="Items per page"),
        db: AsyncSession = Depends(get_db)
):
    """
    Get a paginated list of movies sorted by ID in descending order.
    """
    # Calculate offset
    offset = (page - 1) * per_page

    # Get total count
    count_stmt = select(func.count(MovieModel.id))
    count_result = await db.execute(count_stmt)
    total_items = count_result.scalar_one()

    # Calculate total pages
    total_pages = (total_items + per_page - 1) // per_page

    # Check if page exceeds maximum
    if page > total_pages and total_items > 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    # Get movies for the current page
    stmt = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    movies = result.scalars().all()

    # If no movies found, return 404
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    # Build pagination links
    prev_page = None
    if page > 1:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"

    next_page = None
    if page < total_pages:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    # Convert movies to response format
    movie_items = [
        MovieListItemSchema(
            id=movie.id,
            name=movie.name,
            date=movie.date,
            score=movie.score,
            overview=movie.overview
        )
        for movie in movies
    ]

    return MovieListResponseSchema(
        movies=movie_items,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.post("/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(
        movie_data: MovieCreateRequest,
        db: AsyncSession = Depends(get_db)
):
    """
    Create a new movie with related entities.
    """
    try:
        # Parse date string to date object
        movie_date = datetime.strptime(movie_data.date, "%Y-%m-%d").date()

        # Check for duplicate movie
        existing_movie_stmt = select(MovieModel).where(
            MovieModel.name == movie_data.name,
            MovieModel.date == movie_date
        )
        existing_movie_result = await db.execute(existing_movie_stmt)
        existing_movie = existing_movie_result.scalar_one_or_none()

        if existing_movie:
            raise HTTPException(
                status_code=409,
                detail=f"A movie with the name '{movie_data.name}' and "
                       f"release date '{movie_date}' already exists."
            )

        # Get or create country
        country_stmt = select(CountryModel).where(CountryModel.code == movie_data.country)
        country_result = await db.execute(country_stmt)
        country = country_result.scalar_one_or_none()

        if not country:
            country = CountryModel(code=movie_data.country, name=None)
            db.add(country)
            await db.flush()  # Flush to get the ID

        # Get or create genres
        genres = []
        for genre_name in movie_data.genres:
            genre_stmt = select(GenreModel).where(GenreModel.name == genre_name)
            genre_result = await db.execute(genre_stmt)
            genre = genre_result.scalar_one_or_none()

            if not genre:
                genre = GenreModel(name=genre_name)
                db.add(genre)
                await db.flush()

            genres.append(genre)

        # Get or create actors
        actors = []
        for actor_name in movie_data.actors:
            actor_stmt = select(ActorModel).where(ActorModel.name == actor_name)
            actor_result = await db.execute(actor_stmt)
            actor = actor_result.scalar_one_or_none()

            if not actor:
                actor = ActorModel(name=actor_name)
                db.add(actor)
                await db.flush()

            actors.append(actor)

        # Get or create languages
        languages = []
        for language_name in movie_data.languages:
            language_stmt = select(LanguageModel).where(LanguageModel.name == language_name)
            language_result = await db.execute(language_stmt)
            language = language_result.scalar_one_or_none()

            if not language:
                language = LanguageModel(name=language_name)
                db.add(language)
                await db.flush()

            languages.append(language)

        # Create movie
        movie = MovieModel(
            name=movie_data.name,
            date=movie_date,
            score=movie_data.score,
            overview=movie_data.overview,
            status=MovieStatusEnum(movie_data.status),
            budget=movie_data.budget,
            revenue=movie_data.revenue,
            country_id=country.id,
            genres=genres,
            actors=actors,
            languages=languages
        )

        db.add(movie)
        await db.commit()
        await db.refresh(movie)

        # Load relationships for response
        await db.refresh(movie, ['country', 'genres', 'actors', 'languages'])

        return MovieDetailSchema(
            id=movie.id,
            name=movie.name,
            date=movie.date,
            score=movie.score,
            overview=movie.overview,
            status=movie.status.value,
            budget=float(movie.budget),
            revenue=movie.revenue,
            country={
                "id": movie.country.id,
                "code": movie.country.code,
                "name": movie.country.name
            },
            genres=[
                {"id": genre.id, "name": genre.name}
                for genre in movie.genres
            ],
            actors=[
                {"id": actor.id, "name": actor.name}
                for actor in movie.actors
            ],
            languages=[
                {"id": lang.id, "name": lang.name}
                for lang in movie.languages
            ]
        )

    except HTTPException:
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.get("/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_by_id(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    """
    Get a specific movie by its ID.
    """
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
    movie = result.unique().scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return MovieDetailSchema(
        id=movie.id,
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status.value,
        budget=float(movie.budget),
        revenue=movie.revenue,
        country={
            "id": movie.country.id,
            "code": movie.country.code,
            "name": movie.country.name
        },
        genres=[
            {"id": genre.id, "name": genre.name}
            for genre in movie.genres
        ],
        actors=[
            {"id": actor.id, "name": actor.name}
            for actor in movie.actors
        ],
        languages=[
            {"id": lang.id, "name": lang.name}
            for lang in movie.languages
        ]
    )


@router.delete("/{movie_id}/", status_code=204)
async def delete_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    """
    Delete a specific movie by its ID.
    """
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()


@router.patch("/{movie_id}/", response_model=dict)
async def update_movie(
        movie_id: int,
        update_data: MovieUpdateRequest,
        db: AsyncSession = Depends(get_db)
):
    """
    Update a specific movie by its ID.
    """
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    try:
        # Update only provided fields
        update_dict = update_data.model_dump(exclude_unset=True)

        for field, value in update_dict.items():
            if field == "status" and value is not None:
                setattr(movie, field, MovieStatusEnum(value))
            elif field == "date" and value is not None:
                # Parse date string to date object
                parsed_date = datetime.strptime(value, "%Y-%m-%d").date()
                setattr(movie, field, parsed_date)
            else:
                setattr(movie, field, value)

        await db.commit()

        return {"detail": "Movie updated successfully."}

    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")
