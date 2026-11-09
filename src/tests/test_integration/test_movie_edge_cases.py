import json
from datetime import date, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import event, func, select
from sqlalchemy.exc import IntegrityError

from database.models import (
    ActorModel,
    ActorsMoviesModel,
    CountryModel,
    GenreModel,
    LanguageModel,
    MovieModel,
    MovieStatusEnum,
    MoviesGenresModel,
    MoviesLanguagesModel,
)


MOVIES_URL = "/api/v1/theater/movies/"


@pytest.fixture
def movie_data():
    return {
        "name": "Edge Case Movie",
        "date": "2025-01-01",
        "score": 50,
        "overview": "A movie for testing.",
        "status": "Released",
        "budget": 100,
        "revenue": 200,
        "country": "USA",
        "genres": ["Drama"],
        "actors": ["Test Actor"],
        "languages": ["English"],
    }


@pytest_asyncio.fixture
async def existing_movie_id(db_session):
    country = CountryModel(code="USA", name="United States")
    movie = MovieModel(
        name="Existing Movie", date=date(2025, 1, 1), score=50,
        overview="Original", status=MovieStatusEnum.RELEASED,
        budget=100, revenue=200, country=country,
    )
    db_session.add(movie)
    await db_session.commit()
    return movie.id


@pytest.mark.asyncio
@pytest.mark.parametrize("field,value", [
    ("score", -0.1), ("score", 100.1), ("budget", -0.01),
    ("revenue", -0.01), ("date", "invalid-date"),
    ("status", "Unknown"), ("name", "x" * 256),
])
async def test_create_rejects_invalid_fields(client, movie_data, field, value):
    movie_data[field] = value
    response = await client.post(MOVIES_URL, json=movie_data)
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid input data."}


@pytest.mark.asyncio
async def test_create_rejects_missing_required_field(client, movie_data):
    del movie_data["name"]
    response = await client.post(MOVIES_URL, json=movie_data)
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid input data."}


@pytest.mark.asyncio
@pytest.mark.parametrize("field,value", [
    ("budget", 10_000_000_000_000),
    ("genres", ["x" * 256]),
    ("actors", ["x" * 256]),
    ("languages", ["x" * 256]),
])
async def test_create_rejects_values_exceeding_database_limits(client, movie_data, field, value):
    movie_data[field] = value
    response = await client.post(MOVIES_URL, json=movie_data)
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid input data."}


@pytest.mark.asyncio
async def test_create_rejects_non_finite_revenue(client, movie_data):
    body = json.dumps(movie_data).replace('"revenue": 200', '"revenue": 1e1000')
    response = await client.post(MOVIES_URL, content=body, headers={"content-type": "application/json"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid input data."}


@pytest.mark.asyncio
@pytest.mark.parametrize("score", [0, 100])
async def test_create_accepts_score_and_money_boundaries(client, movie_data, score):
    movie_data.update(score=score, budget=0, revenue=0)
    response = await client.post(MOVIES_URL, json=movie_data)
    assert response.status_code == 201
    assert response.json()["score"] == score
    assert float(response.json()["budget"]) == 0
    assert response.json()["revenue"] == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("days,status", [(364, 201), (367, 400)])
async def test_create_checks_future_date_limit(client, movie_data, days, status):
    movie_data["date"] = (date.today() + timedelta(days=days)).isoformat()
    response = await client.post(MOVIES_URL, json=movie_data)
    assert response.status_code == status
    if status == 400:
        assert response.json() == {"detail": "Invalid input data."}


@pytest.mark.asyncio
@pytest.mark.parametrize("field,value", [
    ("score", -0.1), ("score", 100.1), ("budget", -0.01),
    ("revenue", -0.01), ("date", "invalid-date"),
    ("name", None), ("date", None), ("score", None),
    ("overview", None), ("status", None), ("budget", None),
    ("revenue", None),
])
async def test_patch_rejects_invalid_and_null_fields(client, existing_movie_id, field, value):
    response = await client.patch(f"{MOVIES_URL}{existing_movie_id}/", json={field: value})
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid input data."}


@pytest.mark.asyncio
async def test_create_reuses_related_records(client, movie_data):
    first = await client.post(MOVIES_URL, json=movie_data)
    assert first.status_code == 201
    movie_data["name"] = "Another Movie"
    second = await client.post(MOVIES_URL, json=movie_data)
    assert second.status_code == 201
    first_data, second_data = first.json(), second.json()
    assert first_data["country"]["id"] == second_data["country"]["id"]
    for field in ("genres", "actors", "languages"):
        assert [item["id"] for item in first_data[field]] == [
            item["id"] for item in second_data[field]
        ]


@pytest.mark.asyncio
async def test_create_retries_separate_related_record_conflicts(client, movie_data):
    def fail_once(mapper, connection, target):
        raise IntegrityError("INSERT related record", {}, Exception("unique conflict"))

    event.listen(CountryModel, "before_insert", fail_once, once=True)
    event.listen(GenreModel, "before_insert", fail_once, once=True)
    try:
        response = await client.post(MOVIES_URL, json=movie_data)
    finally:
        for model in (CountryModel, GenreModel):
            if event.contains(model, "before_insert", fail_once):
                event.remove(model, "before_insert", fail_once)

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_rolls_back_related_records_when_movie_insert_fails(client, db_session, movie_data):
    def fail_movie_insert(mapper, connection, target):
        raise IntegrityError("INSERT movie", {}, Exception("insert failed"))

    event.listen(MovieModel, "before_insert", fail_movie_insert)
    try:
        with pytest.raises(IntegrityError):
            await client.post(MOVIES_URL, json=movie_data)
    finally:
        event.remove(MovieModel, "before_insert", fail_movie_insert)

    for model in (CountryModel, GenreModel, ActorModel, LanguageModel, MovieModel):
        assert await db_session.scalar(select(func.count()).select_from(model)) == 0


@pytest.mark.asyncio
async def test_delete_removes_associations_and_returns_empty_body(client, db_session, movie_data):
    created = await client.post(MOVIES_URL, json=movie_data)
    assert created.status_code == 201
    movie_id = created.json()["id"]
    response = await client.delete(f"{MOVIES_URL}{movie_id}/")
    assert response.status_code == 204
    assert response.content == b""
    for table in (MoviesGenresModel, ActorsMoviesModel, MoviesLanguagesModel):
        count = await db_session.scalar(
            select(func.count()).select_from(table).where(table.c.movie_id == movie_id)
        )
        assert count == 0
    for model in (CountryModel, GenreModel, ActorModel, LanguageModel):
        assert await db_session.scalar(select(func.count()).select_from(model)) == 1
