from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from loguru import logger
from backend.config import settings

DATABASE_URL = f"sqlite+aiosqlite:///{settings.database_url}"

engine = create_async_engine(
    DATABASE_URL,
    echo=False
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def init_db():
    from backend.db import models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Lightweight idempotent migration: add columns introduced after a DB
    # was first created. create_all() only creates missing *tables*, never
    # adds columns to an existing one, so a call_logs table made before
    # call_category existed would otherwise reject inserts that set it.
    async with engine.begin() as conn:
        try:
            await conn.exec_driver_sql(
                "ALTER TABLE call_logs ADD COLUMN call_category VARCHAR"
            )
            logger.info("DB migration: added call_category column to call_logs")
        except Exception:
            # column already exists — nothing to do
            pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session