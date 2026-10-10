"""FastAPI application factory and safe error/request metadata handling."""

import logging
import re
from collections.abc import Callable
from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from app.config import Settings, get_settings
from app.db import build_engine, build_session_factory
from app.dependencies import get_db
from app.errors import ApiError
from app.routes import auth, missions, research, simulation, system, world

logger = logging.getLogger("nexorion.api")
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def _error_payload(
    request: Request,
    *,
    code: str,
    message: str,
    details: list[dict[str, object]] | None = None,
    retryable: bool = False,
) -> dict[str, object]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
            "retryable": retryable,
        },
        "request_id": getattr(request.state, "request_id", str(uuid4())),
    }


def _readiness_result(db: Session) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise ApiError(
            503,
            "DEPENDENCY_NOT_READY",
            "A required dependency is not ready.",
            retryable=True,
        ) from exc
    return {"status": "ready"}


def create_app(
    settings: Settings | None = None,
    session_factory: Callable[[], Session] | None = None,
) -> FastAPI:
    app_settings = settings or get_settings()
    engine = None
    if session_factory is None:
        engine = build_engine(app_settings.database_url)
        session_factory = build_session_factory(engine)

    app = FastAPI(
        title="NEXORION API",
        version="0.2.0",
        description=(
            "Authenticated workspace API with a synthetic digital-world graph, "
            "versioned baselines and deterministic registered-fixture simulations. "
            "Live-system execution is not exposed."
        ),
        docs_url=None if app_settings.app_env == "production" else "/docs",
        redoc_url=None if app_settings.app_env == "production" else "/redoc",
        openapi_url=None if app_settings.app_env == "production" else "/openapi.json",
    )
    app.state.settings = app_settings
    app.state.session_factory = session_factory
    app.state.engine = engine

    cors_origins = [origin.strip() for origin in app_settings.cors_allowed_origins.split(",")
                    if origin.strip()]
    if "*" in cors_origins:
        raise ValueError("Credentialed CORS requires explicit origins; wildcard is forbidden.")
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Accept", "Content-Type", "X-Workspace-ID", "X-CSRF-Token",
                           "Idempotency-Key", "X-Request-ID"],
            expose_headers=["X-Request-ID"],
        )

    @app.middleware("http")
    async def request_metadata_and_security_headers(
        request: Request, call_next
    ):  # type: ignore[no-untyped-def]
        supplied_id = request.headers.get("x-request-id", "")
        request_id = supplied_id if _REQUEST_ID_PATTERN.fullmatch(supplied_id) else str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        if request.url.path not in {"/docs", "/redoc"}:
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; frame-ancestors 'none'"
            )
        return response

    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(
                request,
                code=exc.code,
                message=exc.message,
                details=exc.details,
                retryable=exc.retryable,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        safe_details = [
            {
                "loc": [str(part) for part in item.get("loc", ())],
                "msg": str(item.get("msg", "Invalid value.")),
                "type": str(item.get("type", "value_error")),
            }
            for item in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_error_payload(
                request,
                code="REQUEST_VALIDATION_FAILED",
                message="The request did not match the API contract.",
                details=safe_details,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        status_to_code = {
            401: "AUTHENTICATION_REQUIRED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
        }
        message = (
            exc.detail
            if isinstance(exc.detail, str)
            else "The request could not be completed."
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(
                request,
                code=status_to_code.get(exc.status_code, f"HTTP_{exc.status_code}"),
                message=message,
            ),
        )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "unhandled_request_error request_id=%s exception_type=%s",
            getattr(request.state, "request_id", "unknown"),
            type(exc).__name__,
        )
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_payload(
                request,
                code="INTERNAL_ERROR",
                message="The server could not complete the request.",
            ),
        )

    app.include_router(auth.router, prefix="/v1")
    app.include_router(missions.router, prefix="/v1")
    app.include_router(system.router, prefix="/v1")
    app.include_router(world.router, prefix="/v1")
    app.include_router(simulation.router, prefix="/v1")
    app.include_router(research.router, prefix="/v1")

    @app.get("/health", include_in_schema=False)
    def root_health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready", include_in_schema=False)
    def root_ready(db: Session = Depends(get_db)) -> dict[str, str]:
        return _readiness_result(db)

    return app


app = create_app()
