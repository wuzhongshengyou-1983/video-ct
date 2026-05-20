"""订阅 + 订单业务逻辑."""
from __future__ import annotations

import time
import random
import string
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BizException, NotFoundError
from app.models.referrer import ReferrerLink, RewardAccount, RewardTransaction
from app.models.subscription import Order, ProductCatalog, Subscription
from app.models.user import User


def gen_order_no() -> str:
    return f"VCT{int(time.time())}{''.join(random.choices(string.digits, k=4))}"


async def get_active_subscription(db: AsyncSession, user_id: int) -> Subscription | None:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Subscription)
        .where(
            and_(
                Subscription.user_id == user_id,
                Subscription.status == "active",
                Subscription.expires_at > now,
            )
        )
        .order_by(Subscription.expires_at.desc())
    )
    return result.scalar_one_or_none()


async def get_user_tier(db: AsyncSession, user_id: int) -> str:
    """返回 user 当前付费档位: free / pro / max."""
    sub = await get_active_subscription(db, user_id)
    return sub.tier if sub else "free"


async def create_order(
    db: AsyncSession,
    *,
    user: User,
    sku: str,
    use_deduction: bool = False,
    referrer_code: str | None = None,
) -> Order:
    # 1. 查产品
    result = await db.execute(select(ProductCatalog).where(ProductCatalog.sku == sku))
    product = result.scalar_one_or_none()
    if not product or not product.is_active:
        raise NotFoundError("product")

    total = product.price_cny
    deduction = 0

    # 2. 余额抵扣（PRO 月卡满 99 可抵扣）
    if use_deduction and product.tier == "pro":
        acc = await _get_or_create_reward_account(db, user.id)
        max_deduct = min(acc.deduction_balance_cny, total)
        deduction = max_deduct
        acc.deduction_balance_cny -= deduction
        acc.total_deducted_cny += deduction
        db.add(RewardTransaction(
            user_id=user.id,
            txn_type="deduct",
            amount_cny=-deduction,
            balance_after_cny=acc.deduction_balance_cny,
            note=f"订阅抵扣 sku={sku}",
        ))

    paid = total - deduction

    # 3. 推荐人归因
    referred_by = None
    if referrer_code:
        res = await db.execute(
            select(ReferrerLink).where(
                ReferrerLink.link_code == referrer_code,
                ReferrerLink.inviter_id != user.id,
            ).limit(1)
        )
        link = res.scalar_one_or_none()
        if link:
            referred_by = link.inviter_id

    order = Order(
        order_no=gen_order_no(),
        user_id=user.id,
        sku=sku,
        unit_price_cny=product.price_cny,
        quantity=1,
        total_cny=total,
        deduction_cny=deduction,
        paid_cny=paid,
        payment_method="wechat_pay",
        payment_status="pending" if paid > 0 else "paid",  # 全抵扣直接成功
        paid_at=datetime.now(timezone.utc) if paid == 0 else None,
        referred_by_user_id=referred_by,
    )
    db.add(order)
    await db.flush()

    # 全抵扣完成 → 直接激活订阅
    if paid == 0:
        await activate_subscription(db, order)

    return order


async def activate_subscription(db: AsyncSession, order: Order) -> Subscription:
    """订单支付成功后激活订阅."""
    result = await db.execute(select(ProductCatalog).where(ProductCatalog.sku == order.sku))
    product = result.scalar_one()

    now = datetime.now(timezone.utc)
    days = {"monthly": 30, "quarterly": 90, "yearly": 365, "once": 0}.get(product.billing_cycle, 0)

    # 单次产品不创建订阅
    if product.tier in {"single", "addon", "free"}:
        order.payment_status = "paid"
        order.paid_at = now
        return None  # type: ignore

    # 续费叠加
    existing = await get_active_subscription(db, order.user_id)
    if existing and existing.sku == order.sku:
        existing.expires_at = existing.expires_at + timedelta(days=days)
        sub = existing
    else:
        # 升级覆盖
        if existing:
            existing.status = "canceled"
            existing.canceled_at = now
        sub = Subscription(
            user_id=order.user_id,
            sku=order.sku,
            tier=product.tier,
            status="active",
            started_at=now,
            expires_at=now + timedelta(days=days),
            auto_renew=False,
        )
        db.add(sub)

    order.payment_status = "paid"
    order.paid_at = now

    # 触发分享官奖励
    await _process_referral_reward(db, order)

    return sub


async def _get_or_create_reward_account(db: AsyncSession, user_id: int) -> RewardAccount:
    res = await db.execute(select(RewardAccount).where(RewardAccount.user_id == user_id))
    acc = res.scalar_one_or_none()
    if not acc:
        acc = RewardAccount(user_id=user_id)
        db.add(acc)
        await db.flush()
    return acc


async def _process_referral_reward(db: AsyncSession, order: Order) -> None:
    """支付成功后，给推荐人发奖励."""
    from app.config import settings as cfg

    if not order.referred_by_user_id:
        return

    # 找归因记录
    res = await db.execute(
        select(ReferrerLink).where(
            ReferrerLink.inviter_id == order.referred_by_user_id,
            ReferrerLink.invitee_id == order.user_id,
            ReferrerLink.first_paid_at.is_(None),
        ).limit(1)
    )
    link = res.scalar_one_or_none()
    if not link:
        return  # 已奖励过

    # 单价 ≥ 19 才奖励
    if order.paid_cny < 19:
        return

    # 发奖（默认 18 元 · 入抵扣账户）
    reward = cfg.REFERRER_REWARD_CNY
    acc = await _get_or_create_reward_account(db, order.referred_by_user_id)
    acc.deduction_balance_cny += reward
    acc.total_earned_cny += reward

    link.first_paid_at = datetime.now(timezone.utc)
    link.reward_amount_cny = reward
    link.reward_status = "credited"

    db.add(RewardTransaction(
        user_id=order.referred_by_user_id,
        txn_type="earn",
        amount_cny=reward,
        balance_after_cny=acc.deduction_balance_cny,
        related_id=order.order_no,
        note=f"分享官奖励：被推荐人完成订单 {order.order_no}",
    ))

    # 更新分享官等级累计
    from app.models.referrer import ReferrerLevel
    res = await db.execute(select(ReferrerLevel).where(ReferrerLevel.user_id == order.referred_by_user_id))
    level = res.scalar_one_or_none()
    if level:
        level.total_valid_referrals += 1
        level.total_rewards_cny += reward
        # 升级判定
        new_level = _calc_level(level.total_valid_referrals)
        if new_level != level.level:
            level.level = new_level
            level.level_at = datetime.now(timezone.utc)


def _calc_level(count: int) -> str:
    if count >= 101:
        return "diamond"
    if count >= 31:
        return "gold"
    if count >= 11:
        return "silver"
    return "bronze"
