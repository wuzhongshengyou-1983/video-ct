"""微信相关 API 路由 · JS-SDK 签名 + OAuth 授权 URL."""
from __future__ import annotations

from urllib.parse import urlparse

from fastapi import APIRouter, Query

from app.schemas.wechat import JsSdkSignResponse, OAuthUrlResponse
from app.services import wechat_service

router = APIRouter()


# ---------------------------------------------------------------------------
# JS-SDK 签名
# ---------------------------------------------------------------------------
@router.get("/js-sdk-sign", response_model=JsSdkSignResponse)
async def js_sdk_sign(url: str = Query(..., description="当前页面 URL（不含 # 之后）")):
    """获取 wx.config 所需的签名参数.

    前端调用: GET /api/v1/wechat/js-sdk-sign?url=<encodeURIComponent(location.href.split('#')[0])>
    """
    # 清洗 URL：去掉 # 后部分
    parsed = urlparse(url)
    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    if parsed.query:
        clean_url += f"?{parsed.query}"

    result = await wechat_service.generate_js_sdk_sign(clean_url)
    return JsSdkSignResponse(**result)


# ---------------------------------------------------------------------------
# OAuth 授权 URL
# ---------------------------------------------------------------------------
@router.get("/oauth-url", response_model=OAuthUrlResponse)
async def get_oauth_url(
    redirect: str = Query(default="/home", description="授权后回跳的页面路径"),
    ref: str = Query(default=None, description="推荐人 code"),
):
    """获取微信 OAuth 授权 URL.

    前端调用: GET /api/v1/wechat/oauth-url?redirect=/home&ref=ABC123
    返回授权 URL，前端做 location.href 跳转.
    """
    state_extra = {}
    if ref:
        state_extra["referrer_code"] = ref
    url = wechat_service.get_oauth_url(redirect=redirect, state_extra=state_extra or None)
    return OAuthUrlResponse(url=url)
