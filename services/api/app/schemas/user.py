"""用户 schemas."""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class UserPublic(BaseModel):
    id: int
    nickname: str
    avatar_url: str | None = None
    role: str
    is_realname: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileIn(BaseModel):
    nickname: str | None = None
    avatar_url: str | None = None
    track: str | None = None
    platform_main: str | None = None
    follower_count: int | None = None
    bio: str | None = None
    goals: str | None = None


class UserMe(UserPublic):
    phone: str | None = None
    email: str | None = None
    track: str | None = None
    platform_main: str | None = None
    follower_count: int = 0
    subscription_tier: str = "free"
    subscription_expires_at: datetime | None = None
    monthly_free_scans_used: int = 0
    monthly_free_scans_quota: int = 3
    cash_balance_cny: int = 0
    deduction_balance_cny: int = 0
    ticket_balance: int = 0
