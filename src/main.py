from contextlib import asynccontextmanager
from fastapi import FastAPI
from routes.movies import router as movie_router
from database import reset_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    await reset_database()
    yield


app = FastAPI(title="Movies homework", lifespan=lifespan)

app.include_router(
    movie_router,
    prefix="/api/v1/theater/movies",
    tags=["theater"]
)
