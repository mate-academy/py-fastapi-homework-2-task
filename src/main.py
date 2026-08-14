from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from routes import movie_router


app = FastAPI(
    title="Movies homework",
    description="Description of project"
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors = exc.errors()
    has_body_error = any(
        error["loc"] and error["loc"][0] == "body"
        for error in errors
    )
    status_code = (
        status.HTTP_400_BAD_REQUEST
        if has_body_error
        else status.HTTP_422_UNPROCESSABLE_ENTITY
    )

    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder({"detail": errors}),
    )

api_version_prefix = "/api/v1"
app.state.api_version_prefix = api_version_prefix

app.include_router(
    movie_router,
    prefix=f"{api_version_prefix}/theater",
    tags=["theater"],
)
