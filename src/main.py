from fastapi import FastAPI

from routes.movies import router as movies_router


app = FastAPI(
    title="Movies homework",
    description="Description of project"
)

api_version_prefix = "/api/v1"

app.include_router(movies_router, prefix="/api/v1/theater/movies", tags=["movies"])
