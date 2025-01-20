from fastapi import FastAPI
from src.routes.movies import router as movie_router

app = FastAPI(
    title="Movies homework",
    description="Description of project"
)

app.include_router(movie_router, prefix="/api/v1", tags=["theater"])

for route in app.routes:
    print(route.path, route.methods)
