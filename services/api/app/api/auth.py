"""鉴权路由."""
from __future__ import annotations

import json

from fastapi import APIRouter, Query
from fastapi.responses import RedirectResponse
from loguru import logger

from app.config import settings
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


@router.get("/wechat/callback")
async def wechat_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
):
    """微信 OAuth 回调 · code 换 openid → 自动登录 → 回跳页面.

    这是微信服务器调用的端点，用户不会直接访问.
    """
    from sqlalchemy import select
    from app.database import get_db
    from app.models.user import User, UserProfile
    from app.models.referrer import RewardAccount, ReferrerLevel, ReferrerLink, ReferralRecord
    from app.services import wechat_service

    # 解析 state 中的 redirect 和 referrer_code
    redirect_path = "/home"
    referrer_code = None
    try:
        state_data = json.loads(state)
        redirect_path = state_data.get("redirect", "/home")
        referrer_code = state_data.get("referrer_code")
    except (json.JSONDecodeError, TypeError):
        logger.warning(f"[WechatOAuth] invalid state JSON: {state}")

    try:
        oauth_data = await wechat_service.code_to_openid(code)
        openid = oauth_data["openid"]
    except Exception as exc:
        logger.error(f"[WechatOAuth] code_to_openid failed: {exc}")
        if settings.WECHAT_APP_ID.startswith("mock_") or not settings.WECHAT_APP_ID:
            openid = f"mock_openid_{code[:16]}"
        else:
            return RedirectResponse(
                url=f"/login?error=wechat_oauth_failed&redirect={redirect_path}"
            )

    # 登录或注册
    import random as _random
    import string as _string

    db_gen = get_db()
    db = await anext(db_gen)
    try:
        res = await db.execute(select(User).where(User.wechat_openid == openid))
        user = res.scalar_one_or_none()
        is_new = False

        if not user:
            user = User(
                wechat_openid=openid,
                nickname=f"微信用户_{openid[-4:]}",
            )
            db.add(user)
            await db.flush()
            db.add(UserProfile(user_id=user.id))
            db.add(RewardAccount(user_id=user.id))
            db.add(ReferrerLevel(user_id=user.id))
            link_code = "".join(_random.choices(_string.ascii_uppercase + _string.digits, k=8))
            db.add(ReferrerLink(inviter_id=user.id, link_code=link_code))

            # 处理推荐人
            if referrer_code:
                await _process_referrer(db, user.id, referrer_code)

            await db.commit()
            await db.refresh(user)
            is_new = True

        token_data = auth_service.issue_token(user)
        separator = "&" if "?" in redirect_path else "?"
        redirect_url = (
            f"{redirect_path}{separator}"
            f"wechat_token={token_data['access_token']}"
        )

        logger.info(
            f"[WechatOAuth] {'new' if is_new else 'returning'} user "
            f"openid={openid[:16]} redirect={redirect_path}"
        )
        return RedirectResponse(url=redirect_url)

    except Exception as exc:
        logger.exception(f"[WechatOAuth] callback error: {exc}")
        return RedirectResponse(
            url=f"/login?error=wechat_oauth_failed&redirect={redirect_path}"
        )


async def _process_referrer(db, new_user_id: int, referrer_code: str):
    """处理推荐关系."""
    from sqlalchemy import select
    from app.models.referrer import ReferrerLink

    link_res = await db.execute(
        select(ReferrerLink).where(ReferrerLink.link_code == referrer_code)
    )
    link = link_res.scalar_one_or_none()
    if not link:
        return
    db.add(ReferralRecord(
        inviter_id=link.inviter_id,
        invitee_id=new_user_id,
        status="registered",
    ))
    logger.info(f"[WechatOAuth] referral recorded: {link.inviter_id} -> {new_user_id}")


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
