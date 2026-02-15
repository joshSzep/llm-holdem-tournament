"""Database connection and session management."""

import logging
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None


async def get_engine(database_url: str = "sqlite+aiosqlite:///./llm_holdem.db") -> AsyncEngine:
    """Get or create the async database engine.

    Args:
        database_url: SQLAlchemy-style connection URL.

    Returns:
        The async engine instance.
    """
    global _engine
    if _engine is None:
        # Ensure the directory exists for file-based SQLite
        if "sqlite" in database_url and ":///" in database_url:
            db_path = database_url.split("///")[-1]
            if db_path != ":memory:":
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        _engine = create_async_engine(
            database_url,
            echo=False,
        )
        logger.info("Database engine created: %s", database_url)
    return _engine


async def init_db(database_url: str = "sqlite+aiosqlite:///./llm_holdem.db") -> None:
    """Initialize the database — create all tables.

    Args:
        database_url: SQLAlchemy-style connection URL.
    """
    # Import models to ensure they're registered with SQLModel metadata
    import llm_holdem.db.models  # noqa: F401

    engine = await get_engine(database_url)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    logger.info("Database tables created")


async def get_session() -> AsyncSession:
    """Create a new async database session.

    Returns:
        An async session. Caller is responsible for closing.
    """
    engine = await get_engine()
    return AsyncSession(engine)


async def close_db() -> None:
    """Close the database engine and release connections."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        logger.info("Database engine closed")
