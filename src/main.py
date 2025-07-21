from fastapi import FastAPI
from starlette.middleware import Middleware

from routes import movie_router
from routes.movies import PaginationMiddleware

middleware = [Middleware(PaginationMiddleware)]

app = FastAPI(
    title="Movies homework",
    description="Description of project",
    middleware=middleware,
)

api_version_prefix = "/api/v1"

app.include_router(movie_router, prefix=f"{api_version_prefix}/theater", tags=["theater"])
