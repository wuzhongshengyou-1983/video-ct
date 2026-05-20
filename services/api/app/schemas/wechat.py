"""微信相关 Pydantic schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class JsSdkSignResponse(BaseModel):
    """wx.config 签名响应."""
    app_id: str
    timestamp: int
    nonce_str: str
    signature: str
    js_api_list: list[str] = Field(default_factory=lambda: [
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
    ])


class OAuthUrlResponse(BaseModel):
    """微信 OAuth 授权 URL."""
    url: str


class WechatCallbackQuery(BaseModel):
    """OAuth 回调 query 参数."""
    code: str
    state: str  # JSON: {"redirect":"/home","referrer_code":"ABC123"}


class SubscribeMessageRequest(BaseModel):
    """服务端推送订阅消息请求."""
    template_id: str
    page: str = ""
    data: dict  # { "thing1": {"value": "..."}, ... }
    miniprogram_state: str = "formal"  # developer / trial / formal
