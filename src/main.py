from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import (
    request_validation_exception_handler as fastapi_default_handler
)
from fastapi.responses import JSONResponse

from routes import movie_router


app = FastAPI(title="Movies homework", description="Description of project")

api_version_prefix = "/api/v1"


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Check if any validation error came from the request body
    body_errors = [err for err in exc.errors() if err["loc"][0] == "body"]
    if not body_errors:
        # Delegate back to FastAPI’s default (returns 422 on e.g. invalid query params)
        return await fastapi_default_handler(request, exc)
    # Otherwise, return your custom 400 for bad JSON or schema violations
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Invalid input data."},
    )


app.include_router(
    movie_router, prefix=f"{api_version_prefix}/theater", tags=["theater"]
)
