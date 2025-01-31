from typing import Type

from fastapi import HTTPException, status

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from database.models import MovieModel, Base


def extract(field: list[str], model: Type[Base], db: Session) -> list[Base]:
    """
    filed: list of names, model: Model of instances with name
    extract all names from field: add | create in model & add it to list of model instances
    Returns: list of model instances
    """
    instances = []
    for value in field:
        db_model = db.query(model).filter(model.name == value).first()
        if not db_model:
            db_model = model(name=value)
            try:
                db.add(db_model)
                db.commit()
                db.refresh(db_model)
            except SQLAlchemyError as e:
                db.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database Error. " + str(e))
        instances.append(db_model)
    return instances

def get_or_404(id: int, model: Type[MovieModel], db: Session):
    """ get instance by id or 404"""
    db_movie = db.query(model).filter(model.id == id).first()
    if not db_movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")
    return db_movie
