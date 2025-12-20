import datetime

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import GenreModel, ActorModel, LanguageModel, CountryModel
from schemas import movies as schemas
from database import MovieModel
from schemas.movies import MovieUpdateSchema


async def get_all_movies(db: AsyncSession, page: int, per_page: int):
    skip = (page - 1) * per_page

    movies = await db.scalars(
        select(MovieModel).offset(skip).limit(per_page).order_by(MovieModel.id.desc())
    )
    return movies.all()


async def get_movie_by_name_and_date(db: AsyncSession, name: str, date: datetime.date):
    return await db.scalar(
        select(MovieModel).where(MovieModel.name == name, MovieModel.date == date)
    )


async def get_movie_by_id(db: AsyncSession, movie_id: int):
    return await db.scalar(select(MovieModel).where(MovieModel.id == movie_id))


async def get_count_movies(db: AsyncSession):
    return await db.scalar(select(func.count(MovieModel.id)))


async def create_movie(
    db: AsyncSession,
    movie: schemas.MovieCreateSchema,
):
    list_models_names = [movie.genres, movie.actors, movie.languages]
    list_models = [GenreModel, ActorModel, LanguageModel]
    result_list = []
    for list_names, model in zip(list_models_names, list_models):
        existing_objects = await db.scalars(
            select(model).where(model.name.in_(list_names))
        )
        existing_objects = list(existing_objects)
        if len(existing_objects) != len(list_names):
            existing_names = {g.name for g in existing_objects}
            new_names_to_create = [
                name for name in list_names if name not in existing_names
            ]
            new_objects = []
            for name in new_names_to_create:
                object_ = model(name=name)
                db.add(object_)
                new_objects.append(object_)

            await db.flush()
            result_list.append(existing_objects + new_objects)
        else:
            result_list.append(existing_objects)

    country = await db.scalar(
        select(CountryModel).where(CountryModel.code == movie.country)
    )

    if not country:
        country = CountryModel(
            code=movie.country,
        )
        db.add(country)
        await db.flush()

    db_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country_id=country.id,
        genres=result_list[0],
        actors=result_list[1],
        languages=result_list[2],
    )

    db.add(db_movie)
    await db.commit()
    await db.refresh(
        db_movie, attribute_names=["genres", "actors", "languages", "country"]
    )

    return db_movie


async def delete_movie(db: AsyncSession, movie_id: int):
    await db.execute(delete(MovieModel).where(MovieModel.id == movie_id))
    await db.commit()


async def update_movie(db: AsyncSession, movie: MovieUpdateSchema, movie_id: int):
    db_movie = await get_movie_by_id(db=db, movie_id=movie_id)

    update_data = movie.model_dump(exclude_unset=True, exclude_none=True)

    for field, value in update_data.items():
        if field not in ("genres", "actors", "languages", "country"):
            setattr(db_movie, field, value)

    await db.commit()
    await db.refresh(
        db_movie, attribute_names=["genres", "actors", "languages", "country"]
    )

    return db_movie
