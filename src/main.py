from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from exceptions.exceptions import validation_exception_handler
from routes import movie_router


app = FastAPI(
    title="Movies homework",
    description="Description of project"
)

api_version_prefix = "/api/v1"

app.include_router(movie_router, prefix=f"{api_version_prefix}/theater", tags=["theater"])

app.add_exception_handler(RequestValidationError, validation_exception_handler)
