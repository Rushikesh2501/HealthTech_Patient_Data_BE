"""Main FastAPI application entry point.
Configures CORS, security headers, request ID tracing, centralized exception handling,
OpenAPI metadata, and modular routes.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import setup_logging
from app.db.database import check_db_connection
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: configure structured logging
    setup_logging(log_level=settings.LOG_LEVEL, app_env=settings.APP_ENV)
    logger.info("Starting %s in %s environment", settings.APP_NAME, settings.APP_ENV)

    # Validate database connectivity
    db_ok, _ = check_db_connection()
    if db_ok:
        logger.info("Database connection established successfully.")
    else:
        logger.warning(
            "Database connection could not be established at startup. "
            "Ensure PostgreSQL is running and migrations are applied."
        )

    yield

    # Shutdown
    logger.info("Shutting down %s gracefully.", settings.APP_NAME)


OPENAPI_TAGS = [
    {
        "name": "Authentication",
        "description": "JWT authentication, login, refresh tokens, and current user profile.",
    },
    {
        "name": "Patients",
        "description": "Anonymized patient profiles (demographics only, zero PII).",
    },
    {
        "name": "Encounters",
        "description": "Clinical visits, vitals, diagnosis, and treatment logging.",
    },
    {
        "name": "Dashboard",
        "description": "Clinical KPIs, aggregated trends, and graphical visualizer data.",
    },
    {
        "name": "Analytics",
        "description": "Epidemiological analysis, seasonal trends, and demographic breakdowns.",
    },
    {
        "name": "AI Analytics",
        "description": "Gemini AI-powered trend analysis based strictly on aggregated metrics.",
    },
    {
        "name": "AI Medical Chatbot",
        "description": "Conversational medical expert assistant with strict safety guardrails and health-only domain boundaries.",
    },
    {
        "name": "Audit Logs",
        "description": "Immutable audit trails for compliance and access monitoring.",
    },
    {
        "name": "Users",
        "description": "Administrative user management and staff provisioning.",
    },
    {
        "name": "Health",
        "description": "Container liveness and readiness health checks for AWS ALB.",
    },
]

app = FastAPI(
    title=settings.APP_NAME,
    description="Production-grade REST API for rural clinic patient management and analytics.",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production() or settings.DEBUG else None,
    redoc_url="/redoc" if not settings.is_production() or settings.DEBUG else None,
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
)

# ---------------------------------------------------------
# Middleware Stack (Executed in reverse order of addition)
# ---------------------------------------------------------

# 1. Security Headers
app.add_middleware(SecurityHeadersMiddleware)

# 2. CORS - Restrict to authorized client origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time"],
)

# 3. Request ID & Structured Latency Tracking
app.add_middleware(RequestIDMiddleware)


# ---------------------------------------------------------
# Centralized Error Handlers (Section 18)
# ---------------------------------------------------------


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    req_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
            "request_id": req_id,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    req_id = getattr(request.state, "request_id", None)
    # Format errors cleanly
    details = []
    for err in exc.errors():
        loc = " -> ".join([str(loc_item) for loc_item in err.get("loc", [])])
        details.append({"field": loc, "issue": err.get("msg")})

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters or payload",
                "details": {"validation_errors": details},
            },
            "request_id": req_id,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    req_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "HTTP_ERROR",
                "message": str(exc.detail),
                "details": None,
            },
            "request_id": req_id,
        },
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    req_id = getattr(request.state, "request_id", None)
    # Never expose raw database queries or tracebacks in API responses
    logger.error("Database query failure (req_id: %s): %s", req_id, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "DATABASE_ERROR",
                "message": "A database error occurred. The incident has been recorded.",
                "details": None,
            },
            "request_id": req_id,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", None)
    logger.critical("Unhandled unexpected exception (req_id: %s): %s", req_id, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal server error occurred.",
                "details": None,
            },
            "request_id": req_id,
        },
    )


# Mount root API router (includes both direct /api/... and versioned /api/v1/...)
app.include_router(api_router, prefix="/api")


# Friendly root and docs endpoints
@app.get("/", include_in_schema=False)
def root_endpoint():
    if not settings.is_production() or settings.DEBUG:
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url="/docs")
    return {
        "status": "online",
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "api": "/api/v1",
        "health": "/health",
        "ready": "/ready",
    }


@app.get("/doc", include_in_schema=False)
def doc_redirect():
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/docs")


# ALB Health Checks at root level
@app.get("/health", tags=["Health"], summary="Liveness Health Check")
def health_liveness():
    return {"status": "healthy"}


@app.get("/ready", tags=["Health"], summary="Readiness Health Check")
def health_readiness():
    db_ok, err_msg = check_db_connection()
    if not db_ok:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "database": "disconnected", "error": err_msg},
        )
    return {"status": "ready", "database": "connected"}
