from contextlib import asynccontextmanager

from fastapi import FastAPI
from src.database import engine

from src.routes import movie_router


async def lifespan(app: FastAPI):
    try:
        yield
    finally:
        await engine.dispose()

app = FastAPI(
    title="Movies homework",
    description="Description of project",
    lifespan=lifespan
)

api_version_prefix = "/api/v1"

app.include_router(movie_router, prefix=f"{api_version_prefix}/theater", tags=["theater"])
