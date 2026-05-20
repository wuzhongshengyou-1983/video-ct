"""pytest fixtures · 共享测试基础设施."""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app

# 测试用内存数据库
TEST_DATABASE_URL = "sqlite+aiosqlite:///file:test_db?mode=memory&cache=shared&uri=true"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncIterator[AsyncSession]:
    """每次测试独立的数据库 session · 自动建表/拆表."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """FastAPI test client · 注入测试数据库 session."""

    async def _override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def event_loop():
    """session 级 event loop."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============ 共享 mock 数据 ============


def mock_video_meta() -> dict[str, Any]:
    return {
        "url": "https://www.douyin.com/video/123456",
        "platform": "douyin",
        "title": "测试视频标题",
        "duration_sec": 45,
        "publish_at": "2026-05-19T22:13:00+08:00",
        "stats": {
            "play_count": 10000,
            "like_count": 500,
            "comment_count": 80,
            "share_count": 30,
            "collect_count": 100,
        },
        "author": {
            "nickname": "测试博主",
            "follower_count": 5000,
        },
    }


def mock_user_metrics() -> dict[str, float]:
    return {
        "曝光率": 12.0,
        "点赞率": 4.5,
        "评论率": 1.2,
        "转发率": 0.8,
        "收藏率": 3.0,
        "变现率": 0.5,
    }


def mock_benchmark_avg() -> dict[str, float]:
    return {
        "曝光率": 15.0,
        "点赞率": 6.0,
        "评论率": 2.0,
        "转发率": 1.5,
        "收藏率": 4.0,
        "变现率": 1.0,
    }
