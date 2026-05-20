"""鉴权业务逻辑."""
from __future__ import annotations

import random
import string
from datetime import datetime, timedelta, timezone

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import BizException, UnauthorizedError
from app.core.security import create_access_token
from app.models.referrer import ReferrerLink, ReferrerLevel, RewardAccount
from app.models.user import User, UserProfile


# 内存中 OTP（生产请用 Redis）
_otp_store: dict[str, tuple[str, datetime]] = {}


def gen_otp() -> str:
    """生成 6 位数字验证码."""
    return "".join(random.choices(string.digits, k=6))


async def send_otp(phone: str) -> str:
    """发送验证码（开发模式：日志打印；生产：调阿里云短信 API）."""
    code = gen_otp()
    _otp_store[phone] = (code, datetime.now(timezone.utc) + timedelta(minutes=5))
    if settings.ALIYUN_SMS_ACCESS_KEY and settings.ALIYUN_SMS_ACCESS_KEY != "mock_sms_key":
        # TODO: 真实调用阿里云短信
        pass
    logger.info(f"[OTP][DEV] phone={phone} code={code}")
    return code  # 开发模式返回方便测试


def verify_otp(phone: str, code: str) -> bool:
    """开发模式：万能码 0000 通过 + 真实码校验."""
    if settings.NODE_ENV == "development" and code == "0000":
        return True
    entry = _otp_store.get(phone)
    if not entry:
        return False
    saved_code, expire_at = entry
    if datetime.now(timezone.utc) > expire_at:
        _otp_store.pop(phone, None)
        return False
    if saved_code != code:
        return False
    _otp_store.pop(phone, None)
    return True


async def login_or_register_by_phone(
    db: AsyncSession,
    *,
    phone: str,
    referrer_code: str | None = None,
) -> tuple[User, bool]:
    """手机号登录或自动注册. 返回 (user, is_new_user)."""
    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()
    is_new = False

    if not user:
        user = User(phone=phone, nickname=f"博主_{phone[-4:]}")
        db.add(user)
        await db.flush()
        # 创建 profile
        db.add(UserProfile(user_id=user.id))
        # 创建奖励账户
        db.add(RewardAccount(user_id=user.id))
        # 创建分享官记录（默认开通）
        link_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        db.add(ReferrerLevel(user_id=user.id))
        db.add(ReferrerLink(inviter_id=user.id, link_code=link_code))
        is_new = True

        # 归因
        if referrer_code:
            res = await db.execute(
                select(ReferrerLink).where(
                    ReferrerLink.link_code == referrer_code,
                    ReferrerLink.invitee_id.is_(None),
                )
            )
            link = res.scalar_one_or_none()
            if link and link.inviter_id != user.id:
                # 复制一条新的归因记录
                new_link = ReferrerLink(
                    inviter_id=link.inviter_id,
                    invitee_id=user.id,
                    link_code=referrer_code,
                    source="phone_signup",
                )
                db.add(new_link)

        await db.commit()
        await db.refresh(user)

    if not user.is_active:
        raise UnauthorizedError("账号已被禁用")

    token = create_access_token(subject=user.id, extra={"role": user.role})
    return user, is_new


def issue_token(user: User) -> dict:
    token = create_access_token(subject=user.id, extra={"role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.JWT_EXPIRE_MINUTES * 60,
        "user_id": user.id,
        "nickname": user.nickname,
        "role": user.role,
    }
