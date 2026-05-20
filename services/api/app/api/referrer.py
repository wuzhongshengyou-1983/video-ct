"""分享官路由."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import select, func

from app.config import settings
from app.core.exceptions import BizException, NotFoundError
from app.deps import CurrentUser, DbSession
from app.models.referrer import (
    ReferrerLevel, ReferrerLink, RewardAccount, RewardTransaction
)
from app.models.user import User
from app.schemas.referrer import (
    LeaderboardItem, ReferralRecordOut, ReferrerInfoOut, ReferrerLinkOut, WithdrawRequest
)

router = APIRouter()


# 等级升级阈值
LEVEL_THRESHOLDS = {"bronze": 0, "silver": 11, "gold": 31, "diamond": 101}
LEVEL_NAMES = {"bronze": "🥉 铜牌", "silver": "🥈 银牌", "gold": "🥇 金牌", "diamond": "💎 钻石"}


@router.get("/me", response_model=ReferrerInfoOut)
async def my_referrer(db: DbSession, user: CurrentUser):
    # 取已分配 link_code（注册时已创建）
    res = await db.execute(
        select(ReferrerLink).where(
            ReferrerLink.inviter_id == user.id,
            ReferrerLink.invitee_id.is_(None),
        ).limit(1)
    )
    link = res.scalar_one_or_none()
    if not link:
        # 兜底：创建一条
        import random, string
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        link = ReferrerLink(inviter_id=user.id, link_code=code)
        db.add(link)
        await db.commit()

    res = await db.execute(select(ReferrerLevel).where(ReferrerLevel.user_id == user.id))
    level = res.scalar_one_or_none()
    if not level:
        level = ReferrerLevel(user_id=user.id)
        db.add(level)
        await db.commit()
        await db.refresh(level)

    res = await db.execute(select(RewardAccount).where(RewardAccount.user_id == user.id))
    acc = res.scalar_one_or_none() or RewardAccount(user_id=user.id)

    # 距下一级
    next_level = None
    next_at = 0
    for name, thr in LEVEL_THRESHOLDS.items():
        if thr > level.total_valid_referrals:
            next_level = LEVEL_NAMES[name]
            next_at = thr - level.total_valid_referrals
            break

    return ReferrerInfoOut(
        link_code=link.link_code,
        level=LEVEL_NAMES[level.level],
        total_valid_referrals=level.total_valid_referrals,
        total_rewards_cny=level.total_rewards_cny,
        cash_balance_cny=acc.cash_balance_cny,
        deduction_balance_cny=acc.deduction_balance_cny,
        ticket_balance=acc.ticket_balance,
        next_level_at=next_at,
        next_level_name=next_level,
    )


@router.get("/link", response_model=ReferrerLinkOut)
async def get_link(db: DbSession, user: CurrentUser):
    res = await db.execute(
        select(ReferrerLink).where(
            ReferrerLink.inviter_id == user.id, ReferrerLink.invitee_id.is_(None)
        ).limit(1)
    )
    link = res.scalar_one_or_none()
    if not link:
        raise NotFoundError("link")
    base = settings.API_BASE_URL.replace("localhost:8000", "localhost:5173")
    h5_url = f"{base}/invite?ref={link.link_code}"
    return ReferrerLinkOut(
        link_code=link.link_code,
        h5_url=h5_url,
        qr_code_url=f"https://api.qrserver.com/v1/create-qr-code/?data={h5_url}",
        poster_url=f"{settings.API_BASE_URL}/api/v1/referrers/poster.png?code={link.link_code}",
    )


@router.get("/records", response_model=list[ReferralRecordOut])
async def my_records(db: DbSession, user: CurrentUser):
    res = await db.execute(
        select(ReferrerLink, User)
        .join(User, ReferrerLink.invitee_id == User.id)
        .where(ReferrerLink.inviter_id == user.id, ReferrerLink.invitee_id.is_not(None))
        .order_by(ReferrerLink.created_at.desc()).limit(100)
    )
    return [
        ReferralRecordOut(
            invitee_nickname=u.nickname,
            source=l.source,
            first_paid_at=l.first_paid_at,
            reward_amount_cny=l.reward_amount_cny,
            reward_status=l.reward_status,
            created_at=l.created_at,
        )
        for l, u in res.all()
    ]


@router.post("/withdraw")
async def withdraw(payload: WithdrawRequest, db: DbSession, user: CurrentUser):
    """提现到现金（实际生产需对接微信收款 + 实名认证）."""
    if not user.is_realname:
        raise BizException("REALNAME_REQUIRED", "提现需先实名认证", 403)
    if payload.amount_cny < 100:
        raise BizException("MIN_WITHDRAW", "起提金额 100 元", 400)
    res = await db.execute(select(RewardAccount).where(RewardAccount.user_id == user.id))
    acc = res.scalar_one_or_none()
    if not acc or acc.cash_balance_cny < payload.amount_cny:
        raise BizException("INSUFFICIENT", "余额不足", 400)
    acc.cash_balance_cny -= payload.amount_cny
    acc.total_withdrawn_cny += payload.amount_cny
    db.add(RewardTransaction(
        user_id=user.id,
        txn_type="withdraw",
        amount_cny=-payload.amount_cny,
        balance_after_cny=acc.cash_balance_cny,
        note="申请提现",
    ))
    await db.commit()
    return {"ok": True, "remaining_cny": acc.cash_balance_cny}


@router.get("/leaderboard", response_model=list[LeaderboardItem])
async def leaderboard(db: DbSession, limit: int = 30):
    """本月分享榜."""
    now = datetime.now(timezone.utc)
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

    res = await db.execute(
        select(
            ReferrerLink.inviter_id,
            func.count(ReferrerLink.id).label("cnt"),
            func.sum(ReferrerLink.reward_amount_cny).label("rwd"),
        )
        .where(
            ReferrerLink.first_paid_at >= month_start,
            ReferrerLink.invitee_id.is_not(None),
        )
        .group_by(ReferrerLink.inviter_id)
        .order_by(func.count(ReferrerLink.id).desc())
        .limit(limit)
    )
    items = []
    for rank, (uid, cnt, rwd) in enumerate(res.all(), start=1):
        user_res = await db.execute(select(User).where(User.id == uid))
        u = user_res.scalar_one_or_none()
        level_res = await db.execute(select(ReferrerLevel).where(ReferrerLevel.user_id == uid))
        lvl = level_res.scalar_one_or_none()
        items.append(LeaderboardItem(
            rank=rank,
            nickname=u.nickname if u else "匿名",
            avatar_url=u.avatar_url if u else None,
            level=LEVEL_NAMES.get(lvl.level if lvl else "bronze", "🥉 铜牌"),
            monthly_referrals=cnt,
            monthly_rewards_cny=rwd or 0,
        ))
    return items
