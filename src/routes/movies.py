from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from database import get_db
from database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel

from schemas.movies import MovieList

router = APIRouter()


@router.get("/movies/", response_model=MovieList)
def get_movies_list(
        page: int = Query(1, ge=1, description="Page number, must be >= 1"),
        per_page: int = Query(
            10, ge=1, le=20,
            description="Items per page, must be >= 1 and <= 20"
        ),
        db: Session = Depends(get_db)
):
    total_items = db.query(MovieModel).count()
    total_pages = (total_items + per_page - 1) // per_page

    movies = (
        db.query(MovieModel)
        .order_by(desc(MovieModel.id))
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = (f"/theater/movies/?page={page - 1}"
                 f"&per_page={per_page}") if page > 1 else None
    next_page = (f"/theater/movies/?page={page + 1}"
                 f"&per_page={per_page}") if page < total_pages else None

    return MovieList(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )
