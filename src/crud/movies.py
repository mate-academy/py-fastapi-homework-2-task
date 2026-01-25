from sqlalchemy.orm import Session
from sqlalchemy import select, func
from src.database.models import MovieModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieCreateSchema, MovieUpdateSchema


class CRUDMovie:
    def get_by_id(self, db: Session, movie_id: int) -> MovieModel | None:
        return db.get(MovieModel, movie_id)

    def get_multi(self, db: Session, skip: int = 0, limit: int = 10):
        items_query = select(MovieModel).offset(skip).limit(limit)
        items = db.execute(items_query).scalars().all()

        total_query = select(func.count(MovieModel.id))
        total = db.execute(total_query).scalar()

        return items, total

    def create(self, db: Session, obj_in: MovieCreateSchema) -> MovieModel:
        data = obj_in.model_dump(exclude={"genre_ids", "actor_ids", "language_ids"})
        db_obj = MovieModel(**data)

        if obj_in.genre_ids:
            genres = db.execute(select(GenreModel).where(GenreModel.id.in_(obj_in.genre_ids))).scalars().all()
            db_obj.genres = list(genres)

        if obj_in.actor_ids:
            actors = db.execute(select(ActorModel).where(ActorModel.id.in_(obj_in.actor_ids))).scalars().all()
            db_obj.actors = list(actors)

        if obj_in.language_ids:
            langs = db.execute(select(LanguageModel).where(LanguageModel.id.in_(obj_in.language_ids))).scalars().all()
            db_obj.languages = list(langs)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: MovieModel, obj_in: MovieUpdateSchema) -> MovieModel:
        update_data = obj_in.model_dump(exclude_unset=True)

        if "genre_ids" in update_data:
            ids = update_data.pop("genre_ids")
            genres = db.execute(select(GenreModel).where(GenreModel.id.in_(ids))).scalars().all()
            db_obj.genres = list(genres)

        if "actor_ids" in update_data:
            ids = update_data.pop("actor_ids")
            actors = db.execute(select(ActorModel).where(ActorModel.id.in_(ids))).scalars().all()
            db_obj.actors = list(actors)

        if "language_ids" in update_data:
            ids = update_data.pop("language_ids")
            langs = db.execute(select(LanguageModel).where(LanguageModel.id.in_(ids))).scalars().all()
            db_obj.languages = list(langs)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, movie_id: int) -> MovieModel | None:
        obj = db.get(MovieModel, movie_id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj


movie_crud = CRUDMovie()
