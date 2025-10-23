import datetime
from enum import Enum
from sqlalchemy import (
    String,
    Float,
    Text,
    DECIMAL,
    UniqueConstraint,
    Date,
    ForeignKey,
    Table,
    Column,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    mapped_column,
    Mapped,
    relationship,
)
from sqlalchemy import Enum as SQLAlchemyEnum
from typing import (
    Optional,
    List,
    Any,
)


class Base(DeclarativeBase):
    @classmethod
    def default_order_by(cls) -> Optional[List[Any]]:
        return None


class MovieStatusEnum(str, Enum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post PRODUCTION"
    IN_PRODUCTION = "In Production"


MoviesGenresModel = Table(
    "movies_genres",
    Base.metadata,
    Column(
        "movie_id",
        ForeignKey("movies.id_", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "genre_id",
        ForeignKey("genres.id_", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
)

ActorsMoviesModel = Table(
    "actors_movies",
    Base.metadata,
    Column(
        "movie_id",
        ForeignKey("movies.id_", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "actor_id",
        ForeignKey("actors.id_", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
)

MoviesLanguagesModel = Table(
    "movies_languages",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id_", ondelete="CASCADE"), primary_key=True),
    Column(
        "language_id", ForeignKey("languages.id_", ondelete="CASCADE"), primary_key=True
    ),
)


class GenreModel(Base):
    __tablename__ = "genres"

    id_: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel",
        secondary=MoviesGenresModel,
    )

    def __repr__(self) -> str:
        return f"<Genre(name='{self.name}')>"


class ActorModel(Base):
    __tablename__ = "actors"

    id_: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel",
        secondary=ActorsMoviesModel,
    )

    def __repr__(self) -> str:
        return f"<Actor(name='{self.name}')>"


class CountryModel(Base):
    __tablename__ = "countries"

    id_: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel", back_populates="country"
    )

    def __repr__(self) -> str:
        return f"<Country(code='{self.code}', name='{self.name}')>"


class LanguageModel(Base):
    __tablename__ = "languages"

    id_: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel",
        secondary=MoviesLanguagesModel,
    )

    def __repr__(self) -> str:
        return f"<Language(name='{self.name}')>"


class MovieModel(Base):
    __tablename__ = "movies"

    id_: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)

    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    overview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[MovieStatusEnum] = mapped_column(
        SQLAlchemyEnum(MovieStatusEnum), nullable=False
    )
    budget: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 2), nullable=True)
    revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    country_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("countries.id_"), nullable=True
    )
    country: Mapped[Optional["CountryModel"]] = relationship(
        "CountryModel", back_populates="movies"
    )

    genres: Mapped[List["GenreModel"]] = relationship(
        "GenreModel", secondary=MoviesGenresModel, back_populates="movies"
    )

    actors: Mapped[List["ActorModel"]] = relationship(
        "ActorModel", secondary=ActorsMoviesModel, back_populates="movies"
    )

    languages: Mapped[List["LanguageModel"]] = relationship(
        "LanguageModel", secondary=MoviesLanguagesModel, back_populates="movies"
    )

    __table_args__ = (UniqueConstraint("name", "date", name="unique_movie_constraint"),)

    @classmethod
    def default_order_by(cls) -> Optional[List[Any]]:
        return [cls.id_.desc()]

    def __repr__(self) -> str:
        return f"<Movie(name='{self.name}', release_date='{self.date}', score={self.score})>"
