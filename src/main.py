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
async def validate_exceptions_handler(request: Request, exc: RequestValidationError):
    if request.url.path.startswith("/api/v1/theater/movies") and request.method in ("patch", "post"):
        return JSONResponse(
            status_code=400,
            content={"detail": "Invalid input data."}
        )
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors()
        }
    )
