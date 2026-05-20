"""微信服务层 · access_token 缓存 + JS-SDK 签名 + OAuth + 订阅消息推送."""
from __future__ import annotations

import hashlib
import json
import random
import string
import time
from urllib.parse import urlencode

import httpx
from loguru import logger

from app.config import settings

# ---------------------------------------------------------------------------
# Redis 客户端（延迟初始化，开发环境无 Redis 时降级为内存缓存）
# ---------------------------------------------------------------------------
_redis_client = None
_redis_available = False

# 内存缓存回退（开发环境）
_memory_cache: dict[str, tuple[float, str]] = {}  # key -> (expires_at, value)


def _get_redis():
    global _redis_client, _redis_available
    if _redis_client is not None:
        return _redis_client if _redis_available else None

    redis_url = settings.REDIS_URL
    if redis_url:
        try:
            import redis.asyncio as aioredis
            _redis_client = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
            _redis_available = True
            logger.info("[WechatService] Redis connected")
        except Exception as exc:
            logger.warning(f"[WechatService] Redis unavailable, using in-memory cache: {exc}")
            _redis_available = False
    return _redis_client if _redis_available else None


async def _cache_get(key: str) -> str | None:
    """从缓存读取."""
    redis = _get_redis()
    if redis is not None:
        try:
            return await redis.get(key)
        except Exception:
            pass
    # 内存退路
    entry = _memory_cache.get(key)
    if entry is None:
        return None
    expires, val = entry
    if time.monotonic() > expires:
        del _memory_cache[key]
        return None
    return val


async def _cache_set(key: str, value: str, ttl_sec: int) -> None:
    """写入缓存."""
    redis = _get_redis()
    if redis is not None:
        try:
            await redis.setex(key, ttl_sec, value)
            return
        except Exception:
            pass
    # 内存退路
    _memory_cache[key] = (time.monotonic() + ttl_sec, value)


# ---------------------------------------------------------------------------
# Mock / 生产判断
# ---------------------------------------------------------------------------
def _is_mock() -> bool:
    return bool(settings.WECHAT_APP_ID.startswith("mock_") if settings.WECHAT_APP_ID else True)


# ---------------------------------------------------------------------------
# Access Token（带缓存 7200s）
# ---------------------------------------------------------------------------
async def get_access_token() -> str:
    """获取微信公众号 access_token · 生产调微信 API，开发/mock 返回占位."""
    if _is_mock():
        logger.info("[WechatService] mock mode - returning fake access_token")
        return f"mock_access_token_{int(time.time())}"

    cache_key = "wechat:access_token"
    cached = await _cache_get(cache_key)
    if cached:
        return cached

    url = "https://api.weixin.qq.com/cgi-bin/token"
    params = {
        "grant_type": "client_credential",
        "appid": settings.WECHAT_APP_ID,
        "secret": settings.WECHAT_APP_SECRET,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        data = resp.json()
        if "access_token" in data:
            token = data["access_token"]
            expires = data.get("expires_in", 7200) - 300  # 提前 5 分钟过期
            await _cache_set(cache_key, token, max(60, expires))
            logger.info("[WechatService] access_token refreshed")
            return token
        raise RuntimeError(f"获取 access_token 失败: {data}")


# ---------------------------------------------------------------------------
# JS-API Ticket（缓存 7200s）
# ---------------------------------------------------------------------------
async def get_jsapi_ticket() -> str:
    """获取 jsapi_ticket."""
    if _is_mock():
        return f"mock_jsapi_ticket_{int(time.time())}"

    cache_key = "wechat:jsapi_ticket"
    cached = await _cache_get(cache_key)
    if cached:
        return cached

    token = await get_access_token()
    url = "https://api.weixin.qq.com/cgi-bin/ticket/getticket"
    params = {"access_token": token, "type": "jsapi"}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        data = resp.json()
        if data.get("errcode") == 0 and "ticket" in data:
            ticket = data["ticket"]
            expires = data.get("expires_in", 7200) - 300
            await _cache_set(cache_key, ticket, max(60, expires))
            logger.info("[WechatService] jsapi_ticket refreshed")
            return ticket
        raise RuntimeError(f"获取 jsapi_ticket 失败: {data}")


# ---------------------------------------------------------------------------
# JS-SDK 签名生成
# ---------------------------------------------------------------------------
async def generate_js_sdk_sign(url: str) -> dict:
    """生成 wx.config 所需签名参数.

    Args:
        url: 当前页面完整 URL（不含 # 及其后面部分）

    Returns:
        {appId, timestamp, nonceStr, signature, jsApiList}
    """
    if _is_mock():
        # mock 签名 —— 开发环境可用
        ts = int(time.time())
        nonce = "mock_nonce_" + "".join(random.choices(string.ascii_letters + string.digits, k=12))
        raw = f"jsapi_ticket=mock_ticket&noncestr={nonce}&timestamp={ts}&url={url}"
        sig = hashlib.sha1(raw.encode()).hexdigest()
        return {
            "app_id": settings.WECHAT_APP_ID or "mock_app_id",
            "timestamp": ts,
            "nonce_str": nonce,
            "signature": sig,
            "js_api_list": [
                "onMenuShareTimeline",
                "onMenuShareAppMessage",
                "updateAppMessageShareData",
                "updateTimelineShareData",
                "chooseImage",
                "previewImage",
                "uploadImage",
                "getLocation",
                "openLocation",
                "scanQRCode",
                "chooseWXPay",
                "requestSubscribeMessage",
            ],
        }

    ticket = await get_jsapi_ticket()
    ts = int(time.time())
    nonce = "".join(random.choices(string.ascii_letters + string.digits, k=16))
    # 字典序拼接
    raw_str = f"jsapi_ticket={ticket}&noncestr={nonce}&timestamp={ts}&url={url}"
    sig = hashlib.sha1(raw_str.encode()).hexdigest()
    logger.info(f"[WechatService] generated js-sdk sign for url={url[:80]}")
    return {
        "app_id": settings.WECHAT_APP_ID,
        "timestamp": ts,
        "nonce_str": nonce,
        "signature": sig,
        "js_api_list": [
            "onMenuShareTimeline",
            "onMenuShareAppMessage",
            "updateAppMessageShareData",
            "updateTimelineShareData",
            "chooseImage",
            "previewImage",
            "uploadImage",
            "getLocation",
            "openLocation",
            "scanQRCode",
            "chooseWXPay",
            "requestSubscribeMessage",
        ],
    }


# ---------------------------------------------------------------------------
# OAuth 静默登录
# ---------------------------------------------------------------------------
def get_oauth_url(redirect: str, state_extra: dict | None = None) -> str:
    """生成微信 OAuth 授权 URL.

    Args:
        redirect: 回调后跳转的页面路径, 例如 '/home'
        state_extra: 额外的 state 数据, 例如 referrer_code
    """
    callback_base = settings.API_BASE_URL
    state_data = {"redirect": redirect}
    if state_extra:
        state_data.update(state_extra)
    state = json.dumps(state_data, separators=(",", ":"))

    params = {
        "appid": settings.WECHAT_APP_ID,
        "redirect_uri": f"{callback_base}/api/v1/auth/wechat/callback",
        "response_type": "code",
        "scope": "snsapi_userinfo",  # 静默用 snsapi_base, 获取信息用 snsapi_userinfo
        "state": state,
    }
    return f"https://open.weixin.qq.com/connect/oauth2/authorize?{urlencode(params)}#wechat_redirect"


async def code_to_openid(code: str) -> dict:
    """用 code 换取 openid 和 access_token.

    Returns:
        {openid, access_token, refresh_token, unionid, ...}
    """
    if _is_mock():
        logger.info(f"[WechatService] mock code_to_openid code={code[:16]}")
        return {
            "openid": f"mock_openid_{code[:16]}",
            "access_token": f"mock_oauth_token_{int(time.time())}",
            "refresh_token": f"mock_refresh_{int(time.time())}",
            "unionid": f"mock_unionid_{code[:16]}",
            "scope": "snsapi_userinfo",
            "expires_in": 7200,
        }

    url = "https://api.weixin.qq.com/sns/oauth2/access_token"
    params = {
        "appid": settings.WECHAT_APP_ID,
        "secret": settings.WECHAT_APP_SECRET,
        "code": code,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        data = resp.json()
        if "openid" in data:
            logger.info(f"[WechatService] code_to_openid success openid={data['openid']}")
            return data
        raise RuntimeError(f"code 换 openid 失败: {data}")


# ---------------------------------------------------------------------------
# 订阅消息推送（服务端）
# ---------------------------------------------------------------------------
async def send_subscribe_message(
    openid: str,
    template_id: str,
    data: dict,
    page: str = "",
    miniprogram_state: str = "formal",
) -> dict:
    """通过公众号发送订阅消息.

    Args:
        openid: 接收者 openid
        template_id: 模板 ID
        data: 模板数据, 如 {"thing1": {"value": "诊断完成"}, "time2": {"value": "2025-05-20 10:30"}}
        page: 点击跳转的小程序页面路径（可选）
        miniprogram_state: developer / trial / formal

    Returns:
        API 响应 dict
    """
    if _is_mock():
        logger.info(
            f"[WechatService] mock send_subscribe_message "
            f"openid={openid[:16]} template={template_id}"
        )
        return {"errcode": 0, "errmsg": "ok (mock)"}

    token = await get_access_token()
    url = f"https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={token}"
    body = {
        "touser": openid,
        "template_id": template_id,
        "page": page,
        "data": data,
        "miniprogram_state": miniprogram_state,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json=body)
        data = resp.json()
        if data.get("errcode") != 0:
            logger.error(f"[WechatService] send_subscribe_message failed: {data}")
        else:
            logger.info(f"[WechatService] subscribe message sent to {openid[:16]}")
        return data


# ---------------------------------------------------------------------------
# 诊断完成通知便捷方法
# ---------------------------------------------------------------------------
async def notify_diagnosis_complete(
    openid: str,
    report_score: int,
    report_grade: str,
    report_id: int,
) -> dict:
    """发送「诊断完成」订阅消息."""
    grade_map = {"S": "卓越 S", "A": "优秀 A", "B": "良好 B", "C": "一般 C", "D": "较差 D"}
    grade_text = grade_map.get(report_grade, report_grade)

    return await send_subscribe_message(
        openid=openid,
        template_id=settings.WECHAT_TEMPLATE_DIAGNOSIS_DONE,
        data={
            "thing1": {"value": "视频 CT 诊断已生成"},
            "number2": {"value": str(report_score)},
            "thing3": {"value": grade_text},
            "time4": {"value": time.strftime("%Y-%m-%d %H:%M")},
        },
        page=f"pages/report/index?id={report_id}",
    )
