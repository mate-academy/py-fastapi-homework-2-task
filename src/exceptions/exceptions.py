from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    if request.method in ["POST", "PATCH"]:
        return JSONResponse(
            status_code=400,
            content={"detail": exc.errors()},
        )
    return await request_validation_exception_handler(request, exc)
