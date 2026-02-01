from fastapi import FastAPI

from routes import movie_router
from config.settings import API_V1_PREFIX


app = FastAPI(
    title="Movies homework",
    description="Description of project"
)

app.include_router(
    movie_router,
    prefix=f"{API_V1_PREFIX}/theater/movies",
    tags=["movies"]
)
