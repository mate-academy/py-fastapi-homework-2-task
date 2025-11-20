from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_422_UNPROCESSABLE_ENTITY

from routes import movie_router


app = FastAPI(
    title="Movies homework",
    description="Description of project"
)

api_version_prefix = "/api/v1"

app.include_router(movie_router, prefix=f"{api_version_prefix}/theater", tags=["theater"])


async def request_validation_exception_handler(request, exc: RequestValidationError):

    error = exc.errors()[0]

    if error["loc"][0] == "body":
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid input data."}
        )

    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )

app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
