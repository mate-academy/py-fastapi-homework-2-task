from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi import Request
from fastapi.responses import JSONResponse
from routes import movie_router


app = FastAPI(title="Movies homework", description="Description of project")

api_version_prefix = "/api/v1"

app.include_router(
    movie_router, prefix=f"{api_version_prefix}/theater", tags=["theater"]
)


@app.exception_handler(RequestValidationError)
async def exception_handler(request: Request, exc: RequestValidationError):
    if request.method in ("POST", "PATCH"):
        return JSONResponse(
            status_code=400,
            content={"detail": "Invalid input data."},
        )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})
