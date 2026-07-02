"""
app/main.py
STAIL Realty OS — FastAPI application entry point.

Starts the application, configures middleware (CORS, logging),
registers all API routers, and sets up health/readiness endpoints.
"""
import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("realty_os")


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("🚀 STAIL Realty OS API starting up — env=%s", settings.APP_ENV)
    yield
    logger.info("🛑 STAIL Realty OS API shutting down.")


# ── Application factory ───────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "STAIL Realty OS Backend API — AI-native real estate operating system.\n\n"
            "Covers Authentication, Users, Properties, Leads, and 15 AI Agents.\n"
            "Built with FastAPI + PostgreSQL + Redis + Anthropic Claude."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request timing middleware ─────────────────────────────────────────────
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        t0 = time.monotonic()
        response = await call_next(request)
        elapsed_ms = round((time.monotonic() - t0) * 1000, 2)
        response.headers["X-Process-Time-Ms"] = str(elapsed_ms)
        return response

    # ── Global exception handler ──────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception on %s %s", request.method, request.url)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred. Please try again."},
        )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # ── Health endpoints (no auth required) ───────────────────────────────────
    @app.get("/health", tags=["Health"], summary="Basic liveness probe")
    def health() -> dict:
        return {"status": "ok", "version": settings.APP_VERSION}

    @app.get("/readiness", tags=["Health"], summary="Readiness probe — checks DB connectivity")
    def readiness() -> dict:
        from sqlalchemy import text
        from app.db.session import engine
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_status = "ok"
        except Exception as exc:  # noqa: BLE001
            logger.error("DB health check failed: %s", exc)
            db_status = "error"
        overall = "ok" if db_status == "ok" else "degraded"
        return {
            "status": overall,
            "database": db_status,
            "version": settings.APP_VERSION,
        }

    return app


app = create_app()