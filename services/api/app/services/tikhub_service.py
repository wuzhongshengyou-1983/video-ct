# allow-secret
"""TikHub API 服务 · 51 平台视频数据真实采集 · 替代 mock.

API 文档: https://api.tikhub.io/docs
配置来源: ~/999/tools/video-extractor/config.py（火眼金睛项目已验证）
"""
from __future__ import annotations

import hashlib
import hmac
import re
import time
from typing import Any
from urllib.parse import urlparse

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

# ── 平台 URL 识别 ──
PLATFORM_PATTERNS: list[tuple[str, str]] = [
    ("douyin", r"(douyin\.com|iesdouyin\.com|v\.douyin\.com)"),
    ("kuaishou", r"(kuaishou\.com|chenzhongtech\.com|v\.kuaishou\.com)"),
    ("wechat_channels", r"(channels\.weixin\.qq\.com|weixin\.qq\.com)"),
    ("xiaohongshu", r"(xiaohongshu\.com|xhslink\.com|xhslink\.cn)"),
    ("bilibili", r"(bilibili\.com|b23\.tv)"),
    ("tiktok", r"(tiktok\.com)"),
    ("weibo", r"(weibo\.com|t\.cn)"),
    ("youtube", r"(youtube\.com|youtu\.be)"),
    ("instagram", r"(instagram\.com|instagr\.am)"),
    ("zhihu", r"(zhihu\.com)"),
    ("toutiao", r"(toutiao\.com)"),
    ("xigua", r"(xigua\.com|ixigua\.com)"),
    ("pipixia", r"(pipixia\.com)"),
    ("lemon8", r"(lemon8-app\.com)"),
    ("threads", r"(threads\.net)"),
    ("twitter", r"(twitter\.com|x\.com)"),
    ("reddit", r"(reddit\.com|redd\.it)"),
    ("linkedin", r"(linkedin\.com)"),
    ("sora2", r"(sora2\.com)"),
]

PLATFORM_DEFAULT_GROUP: dict[str, str] = {
    "douyin": "douyin_app_v3",
    "kuaishou": "kuaishou_web",
    "wechat_channels": "wechat_channels",
    "xiaohongshu": "xiaohongshu_web",
    "bilibili": "bilibili_web",
    "tiktok": "tiktok_web",
    "weibo": "weibo_web",
    "youtube": "youtube_web",
    "instagram": "instagram",
    "zhihu": "zhihu",
    "toutiao": "toutiao_app",
    "xigua": "xigua",
    "pipixia": "pipixia",
    "lemon8": "lemon8",
    "threads": "threads",
    "twitter": "twitter",
    "reddit": "reddit",
    "linkedin": "linkedin",
    "sora2": "sora2",
}

# 各平台视频详情端点
FETCH_VIDEO_ENDPOINTS: dict[str, str] = {
    "douyin_app_v3": "/api/v1/douyin/app/v3/fetch_one_video_by_share_url",
    "douyin_web": "/api/v1/douyin/web/fetch_one_video_by_share_url",
    "kuaishou_web": "/api/v1/kuaishou/web/fetch_one_video_by_url",
    "kuaishou_app": "/api/v1/kuaishou/app/fetch_one_video_by_url",
    "wechat_channels": "/api/v1/wechat_channels/fetch_video_by_share_url",
    "xiaohongshu_web": "/api/v1/xiaohongshu/web/get_note_info_v5",
    "xiaohongshu_app": "/api/v1/xiaohongshu/app/get_note_info_v2",
    "bilibili_web": "/api/v1/bilibili/web/fetch_one_video_v3",
    "tiktok_web": "/api/v1/tiktok/web/fetch_post_detail",
    "tiktok_app_v3": "/api/v1/tiktok/app/v3/fetch_one_video_by_share_url",
    "weibo_web": "/api/v1/weibo/web_v2/fetch_post_detail",
    "youtube_web": "/api/v1/youtube/web_v2/get_video_info",
}

# 各平台评论端点
FETCH_COMMENTS_ENDPOINTS: dict[str, str] = {
    "douyin_app_v3": "/api/v1/douyin/app/v3/fetch_video_comments",
    "douyin_web": "/api/v1/douyin/web/fetch_video_comments",
    "kuaishou_web": "/api/v1/kuaishou/web/fetch_one_video_comment",
    "wechat_channels": "/api/v1/wechat_channels/fetch_comments",
    "xiaohongshu_web": "/api/v1/xiaohongshu/web/get_note_comments",
    "bilibili_web": "/api/v1/bilibili/web/fetch_video_comments",
    "tiktok_web": "/api/v1/tiktok/web/fetch_post_comment",
}

# 各平台用户/作者信息端点
FETCH_USER_ENDPOINTS: dict[str, str] = {
    "douyin_app_v3": "/api/v1/douyin/app/v3/handler_user_profile",
    "douyin_web": "/api/v1/douyin/web/handler_user_profile",
    "kuaishou_web": "/api/v1/kuaishou/web/fetch_user_info",
    "bilibili_web": "/api/v1/bilibili/web/fetch_user_profile",
    "tiktok_web": "/api/v1/tiktok/web/fetch_user_profile",
}


def detect_platform_tikhub(url: str) -> tuple[str, str]:
    """从 URL 识别平台 → (platform_name, endpoint_group)."""
    for name, pattern in PLATFORM_PATTERNS:
        if re.search(pattern, url, re.IGNORECASE):
            group = PLATFORM_DEFAULT_GROUP.get(name, "")
            return name, group
    return "unknown", ""


def _is_available() -> bool:
    return bool(settings.TIKHUB_API_KEY and not settings.TIKHUB_API_KEY.startswith("mock_"))


class TikHubClient:
    """TikHub API 客户端."""

    def __init__(self) -> None:
        self.client = httpx.AsyncClient(
            base_url=settings.TIKHUB_BASE_URL,
            headers={
                "Authorization": f"Bearer {settings.TIKHUB_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=5))
    async def _get(self, path: str, params: dict | None = None) -> dict:
        resp = await self.client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    async def fetch_video(self, video_url: str) -> dict:
        """拉取视频完整数据 · 返回标准化 VideoMeta."""
        platform, group = detect_platform_tikhub(video_url)
        endpoint = FETCH_VIDEO_ENDPOINTS.get(group)
        if not endpoint:
            logger.warning(f"[TikHub] 不支持的平台/端点组: platform={platform} group={group}")
            return {"error": "unsupported_platform", "platform": platform}

        logger.info(f"[TikHub] 拉取视频 platform={platform} group={group} url={video_url[:60]}")
        raw = await self._get(endpoint, params={"share_url": video_url, "url": video_url})

        # 标准化为内部格式
        return _normalize_video(raw, platform, video_url)

    async def fetch_comments(self, video_url: str, video_id: str = "", cursor: str = "") -> dict:
        """拉取视频评论."""
        platform, group = detect_platform_tikhub(video_url)
        endpoint = FETCH_COMMENTS_ENDPOINTS.get(group)
        if not endpoint:
            return {"comments": [], "cursor": ""}

        params: dict = {"share_url": video_url, "url": video_url}
        if video_id:
            params["video_id"] = video_id
        if cursor:
            params["cursor"] = cursor

        raw = await self._get(endpoint, params=params)
        return _normalize_comments(raw, platform)

    async def fetch_user(self, video_url: str) -> dict:
        """拉取视频作者信息."""
        platform, group = detect_platform_tikhub(video_url)
        endpoint = FETCH_USER_ENDPOINTS.get(group)
        if not endpoint:
            return {"nickname": "", "follower_count": 0}

        raw = await self._get(endpoint, params={"share_url": video_url, "url": video_url})
        return _normalize_user(raw, platform)

    async def close(self) -> None:
        await self.client.aclose()


# ── 标准化器 ──

def _normalize_video(raw: dict, platform: str, original_url: str) -> dict:
    """将 TikHub 各平台异构响应 → 统一 VideoMeta."""
    data = raw.get("data", raw)

    # 尝试从多路径提取
    stats = data.get("statistics", data.get("stats", data.get("video", {})))
    if isinstance(stats, dict):
        pass
    else:
        stats = data

    author = data.get("author", data.get("user", data.get("owner", {})))
    if not isinstance(author, dict):
        author = {}

    video_info = data.get("video", data.get("item", data))

    return {
        "url": original_url,
        "platform": platform,
        "title": str(data.get("title", data.get("desc", data.get("description", "")))),
        "duration_sec": int(_safe_int(data.get("duration", video_info.get("duration", 0))) / 1000)
        if data.get("duration", 0) > 1000
        else _safe_int(data.get("duration", video_info.get("duration", 0))),
        "cover_url": str(data.get("cover", data.get("cover_url", data.get("thumbnail", "")))),
        "publish_at": str(data.get("create_time", data.get("publish_time", data.get("timestamp", "")))),
        "stats": {
            "play_count": _safe_int(stats.get("play_count", stats.get("view_count", stats.get("digg_count", 0)))),
            "like_count": _safe_int(stats.get("like_count", stats.get("digg_count", stats.get("favorite_count", 0)))),
            "comment_count": _safe_int(stats.get("comment_count", stats.get("reply_count", 0))),
            "share_count": _safe_int(stats.get("share_count", stats.get("forward_count", stats.get("repost_count", 0)))),
            "collect_count": _safe_int(stats.get("collect_count", stats.get("favorite_count", stats.get("bookmark_count", 0)))),
        },
        "author": {
            "nickname": str(author.get("nickname", author.get("name", author.get("unique_id", "")))),
            "follower_count": _safe_int(author.get("follower_count", author.get("followers", author.get("fans", 0)))),
            "avatar_url": str(author.get("avatar", author.get("avatar_url", author.get("avatar_thumb", "")))),
            "user_id": str(author.get("uid", author.get("user_id", author.get("sec_uid", "")))),
        },
        "tags": _extract_tags(data),
        "source": "tikhub",
    }


def _normalize_comments(raw: dict, platform: str) -> dict:
    data = raw.get("data", raw)
    comments_list = data.get("comments", data.get("list", data.get("items", [])))
    if not isinstance(comments_list, list):
        comments_list = []

    comments = []
    for c in comments_list[:50]:  # 最多 50 条
        user = c.get("user", c.get("author", {}))
        comments.append({
            "id": str(c.get("cid", c.get("comment_id", c.get("id", "")))),
            "text": str(c.get("text", c.get("content", ""))),
            "like_count": _safe_int(c.get("like_count", c.get("digg_count", 0))),
            "user_nickname": str(user.get("nickname", user.get("name", ""))),
            "create_time": str(c.get("create_time", c.get("time", ""))),
        })

    return {
        "comments": comments,
        "total": _safe_int(data.get("total", data.get("total_count", len(comments)))),
        "cursor": str(data.get("cursor", data.get("next", ""))),
    }


def _normalize_user(raw: dict, platform: str) -> dict:
    data = raw.get("data", raw)
    user = data.get("user", data)
    return {
        "nickname": str(user.get("nickname", user.get("name", ""))),
        "follower_count": _safe_int(user.get("follower_count", user.get("followers", 0))),
        "avatar_url": str(user.get("avatar", user.get("avatar_url", ""))),
        "user_id": str(user.get("uid", user.get("user_id", ""))),
        "bio": str(user.get("signature", user.get("bio", ""))),
        "post_count": _safe_int(user.get("post_count", user.get("video_count", 0))),
    }


def _safe_int(val: Any) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0


def _extract_tags(data: dict) -> list[str]:
    tags = data.get("tags", data.get("hashtags", data.get("challenges", [])))
    if isinstance(tags, list):
        return [str(t.get("name", t.get("title", str(t)))) for t in tags[:10]]
    return []


# ── 公开接口 ──

_tikhub: TikHubClient | None = None


def get_tikhub() -> TikHubClient:
    global _tikhub
    if _tikhub is None:
        _tikhub = TikHubClient()
    return _tikhub


async def fetch_video_meta(video_url: str) -> dict:
    """从 TikHub 真实拉取视频元数据 · 不可用时自动降级 mock."""
    if not _is_available():
        logger.warning("[TikHub] API Key 未配置，无法拉取真实数据")
        return _fallback_mock(video_url)

    try:
        client = get_tikhub()
        meta = await client.fetch_video(video_url)
        if "error" in meta:
            logger.warning(f"[TikHub] 拉取失败: {meta['error']}，降级 mock")
            return _fallback_mock(video_url)
        logger.info(f"[TikHub] ✅ 真实数据: {meta.get('title', 'N/A')[:50]}")
        return meta
    except Exception as exc:
        logger.warning(f"[TikHub] 异常: {exc}，降级 mock")
        return _fallback_mock(video_url)


async def fetch_video_comments(video_url: str, video_id: str = "") -> dict:
    """拉取视频评论 · 不可用时返回空列表."""
    if not _is_available():
        return {"comments": [], "total": 0, "cursor": ""}
    try:
        return await get_tikhub().fetch_comments(video_url, video_id)
    except Exception as exc:
        logger.warning(f"[TikHub] 评论拉取失败: {exc}")
        return {"comments": [], "total": 0, "cursor": ""}


async def fetch_author_info(video_url: str) -> dict:
    """拉取作者信息."""
    if not _is_available():
        return {"nickname": "", "follower_count": 0}
    try:
        return await get_tikhub().fetch_user(video_url)
    except Exception as exc:
        logger.warning(f"[TikHub] 作者信息拉取失败: {exc}")
        return {"nickname": "", "follower_count": 0}


def _fallback_mock(video_url: str) -> dict:
    """TikHub 不可用时的降级 mock · 仅开发期使用."""
    platform = detect_platform_tikhub(video_url)[0]
    logger.info("[TikHub] using fallback mock")
    return {
        "url": video_url,
        "platform": platform,
        "title": "（数据源暂不可用，请稍后重试）",
        "duration_sec": 0,
        "cover_url": "",
        "publish_at": "",
        "stats": {"play_count": 0, "like_count": 0, "comment_count": 0, "share_count": 0, "collect_count": 0},
        "author": {"nickname": "", "follower_count": 0, "avatar_url": "", "user_id": ""},
        "tags": [],
        "source": "fallback_mock",
    }
