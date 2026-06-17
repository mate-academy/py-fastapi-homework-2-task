from fastapi import FastAPI

from routes import movie_router

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


app = FastAPI(
    title="Movies homework",
    description="Description of project"
)

api_version_prefix = "/api/v1"

app.include_router(movie_router, prefix=f"{api_version_prefix}/theater", tags=["theater"])


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Only override the behavior for Create and Update endpoints
    if request.method in ["POST", "PATCH"]:
        return JSONResponse(
            status_code=400,
            content={"detail": "Invalid input data."},
        )

    # For GET requests (like invalid page numbers), fall back to the default 422
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )
