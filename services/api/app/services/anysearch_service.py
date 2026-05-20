# allow-secret
"""AnySearch 跨平台搜索服务 · 竞品分析 + 行业趋势 + 内容搜索.

MCP 配置: ~/.claude/.mcp.json
API: https://api.anysearch.com
"""
from __future__ import annotations

import httpx
from loguru import logger

from app.config import settings


def _is_available() -> bool:
    return bool(settings.ANYSEARCH_API_KEY and not settings.ANYSEARCH_API_KEY.startswith("mock_"))


class AnySearchClient:
    """AnySearch API 客户端."""

    def __init__(self) -> None:
        self.client = httpx.AsyncClient(
            base_url=settings.ANYSEARCH_BASE_URL,
            headers={
                "Authorization": f"Bearer {settings.ANYSEARCH_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )

    async def search(self, query: str, platform: str = "all", limit: int = 10) -> dict:
        """跨平台搜索 · 返回视频/博主/话题."""
        if not _is_available():
            return {"results": [], "source": "mock"}

        try:
            resp = await self.client.post(
                "/search",
                json={"query": query, "platform": platform, "limit": limit},
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info(f"[AnySearch] 搜索完成 query={query} platform={platform}")
            return {"results": data.get("results", data.get("data", [])), "source": "anysearch"}
        except Exception as exc:
            logger.warning(f"[AnySearch] 搜索失败: {exc}")
            return {"results": [], "source": "error", "error": str(exc)}

    async def competitor_analysis(self, track: str, top_n: int = 10) -> dict:
        """竞品分析 · 搜索某赛道头部博主."""
        query = f"{track} 头部博主 爆款视频"
        return await self.search(query, platform="all", limit=top_n)

    async def trend_search(self, keywords: list[str]) -> dict:
        """行业趋势搜索."""
        query = " ".join(keywords)
        return await self.search(query, platform="all", limit=20)

    async def close(self) -> None:
        await self.client.aclose()


_anysearch: AnySearchClient | None = None


def get_anysearch() -> AnySearchClient:
    global _anysearch
    if _anysearch is None:
        _anysearch = AnySearchClient()
    return _anysearch


async def search_competitors(track: str, top_n: int = 10) -> list[dict]:
    """搜索竞品 · 供对标库使用."""
    if not _is_available():
        return []

    try:
        client = get_anysearch()
        result = await client.competitor_analysis(track, top_n)
        items = result.get("results", [])
        return [
            {
                "nickname": str(item.get("nickname", item.get("title", ""))),
                "platform": str(item.get("platform", "")),
                "follower_count": int(item.get("follower_count", item.get("followers", 0))),
                "url": str(item.get("url", "")),
            }
            for item in items[:top_n]
        ]
    except Exception as exc:
        logger.warning(f"[AnySearch] 竞品搜索失败: {exc}")
        return []


async def fetch_industry_trends(keywords: list[str]) -> list[dict]:
    """获取行业趋势."""
    if not _is_available():
        return []

    try:
        client = get_anysearch()
        result = await client.trend_search(keywords)
        return result.get("results", [])
    except Exception as exc:
        logger.warning(f"[AnySearch] 趋势搜索失败: {exc}")
        return []
