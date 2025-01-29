from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from src.database import get_db
from src.database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel


router = APIRouter()


# Write your code here
