from fastapi import FastAPI
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError, HTTPException

from routes import movie_router


app = FastAPI(
    title="Movies homework",
    description="Description of project"
)

api_version_prefix = "/api/v1"

app.include_router(movie_router, prefix=f"{api_version_prefix}/theater", tags=["theater"])


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    if exc.body:
        raise HTTPException(status_code=400, detail="Invalid input data.")
    return await request_validation_exception_handler(request, exc)
