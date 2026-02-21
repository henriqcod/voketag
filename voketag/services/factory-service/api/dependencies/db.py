from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import SQLAlchemyError
import logging

from config.settings import get_settings

Base = declarative_base()
logger = logging.getLogger(__name__)


def get_engine():
    """
    Create SQLAlchemy async engine with connection pooling.
    
    Pool configuration:
    - pool_size: 10 (base connections)
    - max_overflow: 5 (burst capacity)
    - pool_pre_ping: True (validate connections before use)
    - pool_recycle: 3600 (recycle connections after 1 hour)
    """
    settings = get_settings()
    url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return create_async_engine(
        url,
        echo=False,
        pool_size=10,
        max_overflow=5,
        pool_pre_ping=True,  # Validate connections before use
        pool_recycle=3600,   # Recycle stale connections after 1 hour
    )


engine = get_engine()
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_db_session():
    """
    Provide database session with automatic cleanup.
    
    CRITICAL FIX: Ensures session is always closed even if exception occurs
    before yield or during commit/rollback. Uses explicit finally block
    for guaranteed cleanup.
    
    Yields:
        AsyncSession: Database session
        
    Raises:
        SQLAlchemyError: Database errors are re-raised after rollback
    """
    session = None
    try:
        # Create session
        session = async_session()
        
        # Yield to caller
        yield session
        
        # Commit if no exception occurred
        await session.commit()
        logger.debug("Database session committed successfully")
        
    except SQLAlchemyError as e:
        # Rollback on database errors
        if session is not None:
            await session.rollback()
            logger.warning(f"Database session rolled back due to SQLAlchemyError: {e}")
        raise
        
    except Exception as e:
        # Rollback on any other exception
        if session is not None:
            await session.rollback()
            logger.error(f"Database session rolled back due to unexpected exception: {e}", exc_info=True)
        raise
        
    finally:
        # CRITICAL: Always close session, even if exception before yield
        if session is not None:
            await session.close()
            logger.debug("Database session closed")


async def check_db_health() -> bool:
    """
    Check database connection health.
    
    Used by /v1/ready endpoint to verify database connectivity.
    
    Returns:
        bool: True if database is accessible, False otherwise
    """
    try:
        async with get_db_session() as session:
            # Execute simple query to verify connection
            result = await session.execute("SELECT 1")
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def get_pool_stats() -> dict:
    """
    Get current connection pool statistics.
    
    Useful for monitoring and debugging connection leaks.
    
    Returns:
        dict: Pool statistics including size, checked_in, checked_out, etc.
    """
    pool = engine.pool
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total": pool.size() + pool.overflow(),
    }
