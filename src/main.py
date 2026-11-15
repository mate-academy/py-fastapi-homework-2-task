from fastapi import FastAPI, Request
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
    errors = exc.errors()
    is_body_error = any(
        error.get("loc") and error["loc"][0] == "body"
        for error in errors
    )
    if is_body_error:
        return JSONResponse(
            status_code=400,
            content={"detail": "Invalid input data."},
        )
    return JSONResponse(
        status_code=422,
        content={"detail": errors},
    )
