"""数据库引擎 + Session 工厂."""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """所有 ORM 模型基类."""
    pass


def _create_engine() -> AsyncEngine:
    """根据配置创建异步引擎."""
    url = settings.DATABASE_URL
    kwargs: dict = {"echo": False}
    if url.startswith("sqlite"):
        # SQLite 不需要连接池
        from sqlalchemy.pool import NullPool
        kwargs["poolclass"] = NullPool
    else:
        # PostgreSQL（asyncpg）显式连接池配置，避免裸配导致连接耗尽 / 半开连接
        kwargs.update(
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_pre_ping=settings.DB_POOL_PRE_PING,
            pool_timeout=settings.DB_POOL_TIMEOUT,
        )
    return create_async_engine(url, **kwargs)


engine: AsyncEngine = _create_engine()
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """事务上下文."""
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI 依赖：每个请求一个 session."""
    async with SessionLocal() as session:
        yield session
