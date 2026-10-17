import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from algorithms import build_registry
from application.execution import ExecutionBusy, ExecutionRunner, ExecutionUnavailable
from domain.errors import DomainError, InvalidResult, UnknownAlgorithm
from infrastructure.executor import ProcessExecutionRunner
from presentation.middleware import RequestBodyLimit
from presentation.routes import router

logger = logging.getLogger(__name__)
__version__ = "0.1.0"


def error_response(status: int, code: str, message: str) -> JSONResponse:
    headers = {"Retry-After": "1"} if status == 503 else None
    return JSONResponse(
        status_code=status, content={"error": {"code": code, "message": message}}, headers=headers
    )


def create_app(runner: ExecutionRunner | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        owned_runner = None if runner is not None else ProcessExecutionRunner()
        app.state.runner = runner if runner is not None else owned_runner
        try:
            yield
        finally:
            if owned_runner is not None:
                await owned_runner.close()

    app = FastAPI(
        title="AlgoLab API",
        version=__version__,
        description=(
            "Sorting experiments with independently measured performance and replayable traces. "
            "All timings describe server-side Python implementations on this machine."
        ),
        lifespan=lifespan,
    )
    app.state.registry = build_registry()
    app.add_middleware(RequestBodyLimit)
    origins = [origin.strip() for origin in os.getenv("ALGOLAB_CORS_ORIGINS", "").split(",")]
    origins = [origin for origin in origins if origin]
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=False,
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type"],
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
        messages = []
        for detail in error.errors()[:10]:
            location = ".".join(str(part) for part in detail["loc"])
            messages.append(f"{location}: {detail['msg']}")
        return error_response(422, "validation_error", "; ".join(messages))

    @app.exception_handler(DomainError)
    async def domain_error(request: Request, error: DomainError) -> JSONResponse:
        if isinstance(error, InvalidResult):
            logger.error("Algorithm validation failed: %s", error)
            return error_response(500, error.code, "An algorithm failed output validation.")
        status = 404 if isinstance(error, UnknownAlgorithm) else 422
        return error_response(status, error.code, str(error))

    @app.exception_handler(ExecutionBusy)
    async def execution_busy(request: Request, error: ExecutionBusy) -> JSONResponse:
        return error_response(503, "execution_busy", str(error))

    @app.exception_handler(ExecutionUnavailable)
    async def execution_unavailable(request: Request, error: ExecutionUnavailable) -> JSONResponse:
        return error_response(503, "execution_unavailable", str(error))

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, error: Exception) -> JSONResponse:
        logger.error("Unhandled request failure", exc_info=error)
        return error_response(500, "internal_error", "An unexpected server error occurred.")

    @app.get("/health", tags=["Health"])
    async def health() -> dict[str, str]:
        """Process liveness; independent of queued CPU experiments."""
        return {"status": "ok", "service": "AlgoLab", "version": __version__}

    app.include_router(router)
    return app


app = create_app()
