from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import request_validation_exception_handler

from routes import movie_router


app = FastAPI(
    title="Movies homework",
    description="Description of project"
)

api_version_prefix = "/api/v1"

app.include_router(movie_router, prefix=f"{api_version_prefix}/theater", tags=["theater"])


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Перевіряємо, чи це PATCH запит до /movies/{movie_id}/ (шлях закінчується на число та слеш)
    # і чи помилка стосується body (не query параметрів)
    import re
    path_matches = re.search(r'/movies/\d+/$', request.url.path) is not None
    is_patch = request.method == "PATCH"
    # Перевіряємо, чи помилка стосується body (loc містить 'body'), а не query параметрів
    has_body_error = any(error.get('loc', [])[0] == 'body' for error in exc.errors())

    if is_patch and path_matches and has_body_error:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid input data."}
        )
    # Використовуємо стандартний handler FastAPI для інших помилок
    return await request_validation_exception_handler(request, exc)
