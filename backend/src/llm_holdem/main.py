"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from llm_holdem.config import get_settings
from llm_holdem.logging_config import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan handler for startup and shutdown."""
    settings = get_settings()
    setup_logging(log_level=settings.log_level, logfire_token=settings.logfire_token)
    logger.info("LLM Hold'Em Tournament starting up")
    logger.info("Available providers: %s", settings.available_providers())
    yield
    logger.info("LLM Hold'Em Tournament shutting down")


app = FastAPI(
    title="LLM Hold'Em Tournament",
    description="Texas Hold'Em poker with LLM-powered opponents",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
