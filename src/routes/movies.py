from fastapi import APIRouter, Depends, HTTPException, Query, status, Request, Path
from sqlalchemy import select, func, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from schemas import MovieCreateSchema, MovieCreateResponseSchema
from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieListResponseSchema, MovieUpdateSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def list_movies(
        request: Request,
        session: AsyncSession = Depends(get_db),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
):
    total_stmt = select(func.count()).select_from(MovieModel)
    total = (await session.execute(total_stmt)).scalar()

    if total == 0 or (page - 1) * per_page >= total:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")

    stmt = select(MovieModel).order_by(desc(MovieModel.id)).offset((page - 1) * per_page).limit(per_page)
    result = (await session.execute(stmt)).scalars().all()

    base_path = request.url.path

    api_prefix = "/api/v1"
    if base_path.startswith(api_prefix):
        base_path = base_path[len(api_prefix):]

    prev_page = f"{base_path}?page={page - 1}&per_page={per_page}" if page > 1 else None

    next_page = f"{base_path}?page={page + 1}&per_page={per_page}" if page * per_page < total else None
    return MovieListResponseSchema(
        movies=result,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=(total + per_page - 1) // per_page,
        total_items=total,
    )


@router.get("/movies/{movie_id}/", response_model=MovieCreateResponseSchema)
async def get_movie(
        movie_id: int = Path(..., ge=1),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(MovieModel).options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    movie = result.unique().scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.post("/movies/", status_code=status.HTTP_201_CREATED)
async def create_movie(
        movie_data: MovieCreateSchema,
        db: AsyncSession = Depends(get_db)
) -> MovieCreateResponseSchema:
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


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
        movie_id: int = Path(..., ge=1),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.unique().scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/")
async def update_movie(
        movie_id: int,
        data: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.unique().scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    update_data = data.model_dump(exclude_unset=True)

    try:
        for field, value in update_data.items():
            setattr(movie, field, value)

        await db.commit()
        return {"detail": "Movie updated successfully."}
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data."
        )
