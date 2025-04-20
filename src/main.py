import fastapi
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST


from routes import movie_router


app = FastAPI(
    title="Movies homework",
    description="Description of project"
)

api_version_prefix = "/api/v1"

app.include_router(movie_router, prefix=f"{api_version_prefix}/theater", tags=["theater"])


# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request: fastapi.Request, exc: RequestValidationError):
#     return JSONResponse(
#         status_code=HTTP_400_BAD_REQUEST,
#         content={"detail": "Invalid input data."}
#     )
