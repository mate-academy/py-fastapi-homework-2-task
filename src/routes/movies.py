from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy import desc, select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import (
    CountryModel,
    GenreModel,
    LanguageModel,
    ActorModel,
)
from schemas.movies import (
    MovieListItemSchema,
    MovieDetailSchema,
    MovieCreateSchema,
    MovieListResponseSchema, MovieUpdateSchema,
)

router = APIRouter()


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def retrieve_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
) -> MovieDetailSchema:
    result = await (db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    ))
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return MovieDetailSchema.model_validate(movie)


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_list_of_movies(
        db: AsyncSession = Depends(get_db),
        page: int = Query(ge=1, default=1),
        per_page: int = Query(ge=1, le=20, default=10)
) -> MovieListResponseSchema:
    result = await (db.execute(select(MovieModel)
                               .order_by(desc(MovieModel.id))
                               .limit(per_page)
                               .offset((page - 1) * per_page)
                               ))
    movies = result.scalars().all()

    total_items_result = await db.execute(select(func.count(MovieModel.id)))
    total_items = total_items_result.scalar()
    total_pages = total_items // per_page + (
        1 if total_items % per_page != 0 else 0
    )

    if page <= 1:
        prev_page = None
    else:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"

    if page >= total_pages:
        next_page = None
    else:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    return MovieListResponseSchema(
        movies=[MovieListItemSchema.model_validate(movie) for movie in movies],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(
        movie: MovieCreateSchema,
        db: AsyncSession = Depends(get_db)
) -> MovieDetailSchema | HTTPException:
    movie_exist_check = await db.execute(
        select(MovieModel).where(
            (MovieModel.name == movie.name),
            (MovieModel.date == movie.date),
        )
    )
    if movie_exist_check.scalars().first():
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie.name}' and release date "
                f"'{movie.date}' already exists."
            )
        )

    try:
        country_res = await db.execute(
            select(CountryModel).where(CountryModel.code == movie.country)
        )
        country = country_res.scalars().first()
        if not country:
            country = CountryModel(code=movie.country)
            db.add(country)
            await db.flush()

        genres = []
        for genre_name in movie.genres:
            genre = await db.execute(
                select(GenreModel).where(GenreModel.name == genre_name)
            )
            genre = genre.scalars().first()

            if not genre:
                genre = GenreModel(name=genre_name)
                db.add(genre)
                await db.flush()

            genres.append(genre)

        actors = []
        for actor_name in movie.actors:
            actor = await db.execute(
                select(ActorModel).where(ActorModel.name == actor_name)
            )
            actor = actor.scalars().first()

            if not actor:
                actor = ActorModel(name=actor_name)
                db.add(actor)
                await db.flush()

            actors.append(actor)

        languages = []
        for language_name in movie.languages:
            language = await db.execute(
                select(LanguageModel).where(LanguageModel.name == language_name)
            )
            language = language.scalars().first()

            if not language:
                language = LanguageModel(name=language_name)
                db.add(language)
                await db.flush()

            languages.append(language)

        new_movie = MovieModel(
            name=movie.name,
            date=movie.date,
            score=movie.score,
            overview=movie.overview,
            status=movie.status,
            budget=movie.budget,
            revenue=movie.revenue,
            country=country,
            genres=genres,
            actors=actors,
            languages=languages
        )

        db.add(new_movie)
        await db.commit()
        await db.refresh(new_movie, [
            "genres", "actors", "languages"
        ])
        return MovieDetailSchema.model_validate(new_movie)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.patch("/movies/{movie_id}/")
async def update_movie(
        movie_id: int,
        movie: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie_to_update = result.scalars().first()

    if not movie_to_update:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    try:
        for field, value in movie.model_dump(exclude_unset=True).items():
            setattr(movie_to_update, field, value)

        await db.commit()
        await db.refresh(movie_to_update)
        return {"detail": "Movie updated successfully."}

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.delete("/movies/{movie_id}/", status_code=204)
async def remove_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(
        MovieModel.id == movie_id
    ))
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()
