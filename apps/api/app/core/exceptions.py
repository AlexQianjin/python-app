from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class ApplicationError(Exception):
    status_code = 500
    detail = "Internal server error"


class ProductNotFoundError(ApplicationError):
    status_code = 404
    detail = "Product not found"


class DuplicateSKUError(ApplicationError):
    status_code = 409
    detail = "SKU already exists"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApplicationError)
    async def handle_application_error(
        _request: Request, exc: ApplicationError
    ) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
