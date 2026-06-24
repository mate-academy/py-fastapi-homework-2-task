from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from routes import movie_router

app = FastAPI(
    title="Movies homework",
    description="Description of project"
)

api_version_prefix = "/api/v1"

app.include_router(movie_router, prefix=f"{api_version_prefix}/theater", tags=["theater"])


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Check if the validation error originates from the request body
    is_body_error = any(err.get("loc", [])[0] == "body" for err in exc.errors())

    if is_body_error:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid input data."}
        )

    # Standard 422 response for query/path parameter validation
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )
