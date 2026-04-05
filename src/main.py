from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from routes import movie_router

app = FastAPI(title="Movies homework", description="Description of project")


# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(_, exc: RequestValidationError):
#     return JSONResponse(
#         status_code=status.HTTP_400_BAD_REQUEST,
#         content={"detail": exc.errors()}
#     )

api_version_prefix = "/api/v1"

app.include_router(
    movie_router, prefix=f"{api_version_prefix}/theater/movies", tags=["theater"]
)
