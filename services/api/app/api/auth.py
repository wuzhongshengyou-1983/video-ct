"""鉴权路由."""
from __future__ import annotations

from fastapi import APIRouter

from app.core.exceptions import UnauthorizedError
from app.deps import DbSession, CurrentUser
from app.schemas.auth import (
    PhoneOTPRequest, PhoneOTPVerify, TokenResponse, WechatLoginRequest
)
from app.schemas.user import UserMe
from app.services import auth_service

router = APIRouter()


@router.post("/otp/send")
async def send_otp(payload: PhoneOTPRequest):
    """发送手机验证码（开发模式 dev_code 字段直接返回，生产去掉）."""
    code = await auth_service.send_otp(payload.phone)
    return {"sent": True, "dev_code": code}


@router.post("/otp/verify", response_model=TokenResponse)
async def verify_otp(payload: PhoneOTPVerify, db: DbSession):
    if not auth_service.verify_otp(payload.phone, payload.code):
        raise UnauthorizedError("验证码错误或已过期")
    user, is_new = await auth_service.login_or_register_by_phone(
        db, phone=payload.phone, referrer_code=payload.referrer_code
    )
    token = auth_service.issue_token(user)
    return TokenResponse(**token, is_new_user=is_new)


@router.post("/wechat/login", response_model=TokenResponse)
async def wechat_login(payload: WechatLoginRequest, db: DbSession):
    """微信登录 · mock：把 code 当作 openid."""
    from sqlalchemy import select
    from app.models.user import User, UserProfile
    from app.models.referrer import RewardAccount, ReferrerLevel, ReferrerLink
    import random, string

    fake_openid = f"mock_openid_{payload.code[:16]}"
    res = await db.execute(select(User).where(User.wechat_openid == fake_openid))
    user = res.scalar_one_or_none()
    is_new = False
    if not user:
        user = User(wechat_openid=fake_openid, nickname=f"微信用户_{fake_openid[-4:]}")
        db.add(user)
        await db.flush()
        db.add(UserProfile(user_id=user.id))
        db.add(RewardAccount(user_id=user.id))
        db.add(ReferrerLevel(user_id=user.id))
        link_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        db.add(ReferrerLink(inviter_id=user.id, link_code=link_code))
        await db.commit()
        await db.refresh(user)
        is_new = True
    token = auth_service.issue_token(user)
    return TokenResponse(**token, is_new_user=is_new)


@router.get("/me", response_model=UserMe)
async def get_me(db: DbSession, user: CurrentUser):
    from sqlalchemy import select
    from app.models.referrer import RewardAccount
    from app.models.user import UserProfile
    from app.services.subscription_service import get_active_subscription
    from app.services.diagnosis_service import check_quota
    from app.config import settings
    from datetime import datetime, timezone

    prof_res = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    prof = prof_res.scalar_one_or_none()
    acc_res = await db.execute(select(RewardAccount).where(RewardAccount.user_id == user.id))
    acc = acc_res.scalar_one_or_none()
    sub = await get_active_subscription(db, user.id)

    # 配额使用情况（不抛异常）
    try:
        _, used = await check_quota(db, user)
    except Exception:
        used = settings.FREE_MONTHLY_SCANS  # 已用满

    return UserMe(
        id=user.id,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        role=user.role,
        is_realname=user.is_realname,
        created_at=user.created_at,
        phone=user.phone,
        email=user.email,
        track=prof.track if prof else None,
        platform_main=prof.platform_main if prof else None,
        follower_count=prof.follower_count if prof else 0,
        subscription_tier=sub.tier if sub else "free",
        subscription_expires_at=sub.expires_at if sub else None,
        monthly_free_scans_used=used,
        monthly_free_scans_quota=settings.FREE_MONTHLY_SCANS,
        cash_balance_cny=acc.cash_balance_cny if acc else 0,
        deduction_balance_cny=acc.deduction_balance_cny if acc else 0,
        ticket_balance=acc.ticket_balance if acc else 0,
    )
