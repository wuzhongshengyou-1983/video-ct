"""分享官 schemas."""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class ReferrerInfoOut(BaseModel):
    link_code: str
    level: str
    total_valid_referrals: int
    total_rewards_cny: int
    cash_balance_cny: int
    deduction_balance_cny: int
    ticket_balance: int
    next_level_at: int  # 距离下一等级还需多少推荐
    next_level_name: str | None = None


class ReferrerLinkOut(BaseModel):
    link_code: str
    h5_url: str
    qr_code_url: str
    poster_url: str


class ReferralRecordOut(BaseModel):
    invitee_nickname: str
    source: str | None
    first_paid_at: datetime | None
    reward_amount_cny: int
    reward_status: str
    created_at: datetime


class WithdrawRequest(BaseModel):
    amount_cny: int


class LeaderboardItem(BaseModel):
    rank: int
    nickname: str
    avatar_url: str | None
    level: str
    monthly_referrals: int
    monthly_rewards_cny: int
