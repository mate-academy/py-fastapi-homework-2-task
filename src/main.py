from fastapi import FastAPI

from src.routes.movies import router as movie_router

app = FastAPI(title="Movies homework", description="Description of project")

api_version_prefix = "/api/v1"

app.include_router(
    movie_router, prefix=f"{api_version_prefix}/theater", tags=["theater"]
)
