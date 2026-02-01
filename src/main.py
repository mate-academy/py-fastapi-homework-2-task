from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from routes import movie_router

app = FastAPI(title="Movies homework", description="Description of project")

api_version_prefix = "/api/v1"

#
# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(
#     request: Request,
#     exc: RequestValidationError,
# ):
#     if "/movies/" in request.url.path:
#         return JSONResponse(
#             status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#             content={"detail": "Input should be greater than or equal to 1"},
#         )
#
#     return JSONResponse(
#         status_code=status.HTTP_400_BAD_REQUEST,
#         content={"detail": "Invalid input data."},
#     )


app.include_router(
    movie_router, prefix=f"{api_version_prefix}/theater", tags=["theater"]
)
