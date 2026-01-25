from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from src.database.models import MovieModel, GenreModel, ActorModel, LanguageModel, CountryModel
from schemas.movies import MovieCreateSchema


class CRUDMovie:
    async def create(self, db: AsyncSession, obj_in: MovieCreateSchema) -> MovieModel:
        data = obj_in.model_dump(exclude={"genres", "actors", "languages", "country"})

        country_stmt = select(CountryModel).where(CountryModel.code == obj_in.country)
        country_res = await db.execute(country_stmt)
        country = country_res.scalar_one_or_none()

        if not country:
            country = CountryModel(code=obj_in.country)
            db.add(country)
            await db.flush()

        db_obj = MovieModel(**data, country_id=country.id)

        async def get_or_create_related(model, names):
            objs = []
            for name in names:
                stmt = select(model).where(model.name == name)
                res = await db.execute(stmt)
                obj = res.scalar_one_or_none()

                if not obj:
                    obj = model(name=name)
                    db.add(obj)
                objs.append(obj)
            return objs

        if obj_in.genres:
            db_obj.genres = await get_or_create_related(GenreModel, obj_in.genres)

        if obj_in.actors:
            db_obj.actors = await get_or_create_related(ActorModel, obj_in.actors)

        if obj_in.languages:
            db_obj.languages = await get_or_create_related(LanguageModel, obj_in.languages)

        db.add(db_obj)
        await db.commit()

        final_stmt = (
            select(MovieModel)
            .where(MovieModel.id == db_obj.id)
            .options(
                selectinload(MovieModel.genres),
                selectinload(MovieModel.actors),
                selectinload(MovieModel.languages),
                selectinload(MovieModel.country)
            )
        )
        final_res = await db.execute(final_stmt)
        return final_res.scalar_one()


movie_crud = CRUDMovie()
