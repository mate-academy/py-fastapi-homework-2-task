from fastapi import FastAPI

from config.settings import api_version_prefix
from routes import movie_router


app = FastAPI(
    title="Movies homework",
    description="Description of project"
)


app.include_router(movie_router, prefix=f"{api_version_prefix}/theater", tags=["theater"])
