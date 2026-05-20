"""鉴权 schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class PhoneOTPRequest(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")


class PhoneOTPVerify(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    code: str = Field(..., min_length=4, max_length=6)
    referrer_code: str | None = None


class PasswordLogin(BaseModel):
    identifier: str  # phone / email
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    nickname: str
    role: str
    is_new_user: bool = False


class WechatLoginRequest(BaseModel):
    code: str  # wx.login() 拿到的 code
    referrer_code: str | None = None
