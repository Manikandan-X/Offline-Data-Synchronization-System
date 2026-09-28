from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    database_exception_handler,
    general_exception_handler,
    validation_exception_handler,
)
from app.core.logging import setup_logging
from app.routers.auth import router as auth_router
from app.routers.user import router as user_router
from app.routers.record import router as record_router
from app.routers.sync import router as sync_router
from app.routers.sync_history import router as sync_history_router
from app.routers.conflict import router as conflict_router
from app.routers.dashboard import router as dashboard_router
from app.routers.audit_log import router as audit_log_router

setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle.
    """
    logger.info(
        "Starting %s version %s",
        settings.app_name,
        settings.app_version,
    )

    yield

    logger.info(
        "Shutting down %s",
        settings.app_name,
    )


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Offline-First Data Synchronization System"
    ),
    lifespan=lifespan,
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Global Exception Handlers
# --------------------------------------------------

app.add_exception_handler(
    AppException,
    app_exception_handler,
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.add_exception_handler(
    SQLAlchemyError,
    database_exception_handler,
)

app.add_exception_handler(
    Exception,
    general_exception_handler,
)


# --------------------------------------------------
# Routers
# --------------------------------------------------

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(record_router)
app.include_router(sync_router)
app.include_router(sync_history_router)
app.include_router(conflict_router)
app.include_router(dashboard_router)
app.include_router(audit_log_router)

# --------------------------------------------------
# Health Check
# --------------------------------------------------

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "application": settings.app_name,
        "version": settings.app_version,
    }