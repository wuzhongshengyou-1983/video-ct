"""支付回调 webhook · 微信 → 验签 → 激活订阅 → 分享官奖励 → 通知.

微信支付回调链路：
  1. payment_service.verify_wechat_callback()     验签 + 提取订单号
  2. 查 Order                                       确保订单存在
  3. subscription_service.activate_subscription()  激活订阅
  4. subscription_service._process_referral_reward() 分享官奖励（在 activate 内部触发）
  5. 发送通知                                       小程序订阅消息 / 短信
  6. 返回 200 SUCCESS                               微信要求的应答格式
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Request
from loguru import logger
from sqlalchemy import select

from app.database import get_db
from app.models.subscription import Order
from app.services import payment_service, subscription_service

router = APIRouter()


@router.post("/wechat/pay")
async def wechat_pay_callback(request: Request):
    """微信支付 v3 回调通知 · POST /api/v1/webhooks/wechat/pay.

    微信要求:
      - 5 秒内返回 200/204（否则重试）
      - 验签失败返回 400（不重试）
      - 业务失败但验签通过返回 200 但 code=FAIL（避免重复通知）
    """
    # 1. 读取 headers + body
    raw_headers: dict[str, str] = {k.lower(): v for k, v in request.headers.items()}
    body = await request.body()
    body_str = body.decode("utf-8")

    logger.info("[WEBHOOK] 收到微信支付回调 headers={}", raw_headers)

    # 2. 验签 + 提取订单号
    ok, order_no = await payment_service.verify_wechat_callback(raw_headers, body_str)

    if not ok or not order_no:
        logger.warning("[WEBHOOK] 微信支付回调验签失败")
        return {"code": "FAIL", "message": "signature verification failed"}

    logger.info("[WEBHOOK] 验签通过 order_no={}", order_no)

    # 3. 查订单
    async for db in get_db():
        res = await db.execute(select(Order).where(Order.order_no == order_no))
        order = res.scalar_one_or_none()

        if not order:
            logger.error("[WEBHOOK] 未找到订单 order_no={}", order_no)
            return {"code": "FAIL", "message": "order not found"}

        # 防止重复处理（幂等）
        if order.payment_status == "paid":
            logger.info("[WEBHOOK] 订单已支付（幂等） order_no={}", order_no)
            return {"code": "SUCCESS", "message": "already paid"}

        # 4. 标记支付 + 激活订阅
        try:
            await subscription_service.activate_subscription(db, order)
            # activate_subscription 内部已调用 _process_referral_reward
            await db.commit()
            logger.info("[WEBHOOK] 订阅激活成功 order_no={} user_id={}", order_no, order.user_id)
        except Exception as exc:
            logger.error("[WEBHOOK] 激活订阅失败 order_no={}: {}", order_no, exc)
            await db.rollback()
            return {"code": "FAIL", "message": f"activate failed: {exc}"}

        # 5. 发送通知（异步，不阻塞回调应答）
        try:
            await _notify_payment_success(order)
        except Exception as exc:
            logger.warning("[WEBHOOK] 通知发送失败（不影响主流程）: {}", exc)

        # 6. 返回微信要求的成功应答
        return {"code": "SUCCESS", "message": "OK"}


async def _notify_payment_success(order: Order) -> None:
    """支付成功后发送通知（订阅消息 / 短信）.

    当前排优先级:
      1. 微信小程序订阅消息（有 openid 时）
      2. 降级：日志记录（供后续手动通知）
    """
    from app.services.notification import notify_payment_success as _notify

    await _notify(
        user_id=order.user_id,
        order_no=order.order_no,
    )
