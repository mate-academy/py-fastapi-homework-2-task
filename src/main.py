from fastapi import FastAPI

from src.routes import movie_router


app = FastAPI(
    title="Movies homework",
    description="Description of project"
)

api_version_prefix = "/api/v1"

app.include_router(
    movie_router,
    prefix=f"{api_version_prefix}/theater",
    tags=["theater"]
)


@app.get("/")
async def root():
    return {"message": "Welcome to Movie Theater API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
