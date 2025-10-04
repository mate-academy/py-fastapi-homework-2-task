from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from routes import movie_router


app = FastAPI(
    title="Movies homework",
    description="Description of project"
)

api_version_prefix = "/api/v1"

app.include_router(movie_router, prefix=f"{api_version_prefix}/theater", tags=["theater"])


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request, exc: RequestValidationError):
    if request.method in {"POST", "PATCH"} and "/movies/" in str(request.url.path):
        return JSONResponse(status_code=400, content={"detail": "Invalid input data."})
    return JSONResponse(status_code=422, content={"detail": exc.errors()})
