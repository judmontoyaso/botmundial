"""BotMundial – FastAPI application entry point."""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import analysis, matches, predictions, teams
from app.services import data_service

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan context manager
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle for the application."""
    settings = get_settings()
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)

    # Pre-load data at startup
    data_service.load_teams()
    data_service.load_matches()
    logger.info(
        "Loaded %d teams and %d matches",
        len(data_service.load_teams()),
        len(data_service.load_matches()),
    )

    yield  # Application runs here

    logger.info("Shutting down %s", settings.APP_NAME)


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Backend API for BotMundial – a World Cup 2026 analysis dashboard "
        "with AI-powered predictions and polla scoring."
    ),
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Health check (root level)
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# ---------------------------------------------------------------------------
# Mount routers under /api prefix
# ---------------------------------------------------------------------------
app.include_router(teams.router, prefix="/api")
app.include_router(matches.router, prefix="/api")
app.include_router(predictions.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")
