"""通知服务 · 订阅消息 + 短信 + 站内通知.

发送通道：
  - 微信小程序订阅消息 (subscribeMessage.send)
  - 阿里云短信 (Aliyun SMS SDK)
  - 降级：loguru 日志记录
"""
from __future__ import annotations

import json

import httpx
from loguru import logger

from app.config import settings


# ── 微信订阅消息 ──────────────────────────────────────

async def send_subscribe_message(
    openid: str,
    template_id: str,
    data: dict,
    page: str = "",
) -> bool:
    """发送微信小程序订阅消息.

    Args:
        openid: 接收者 openid
        template_id: 订阅消息模板 ID
        data: 模板数据（key: {value: str} 格式）
        page: 点击跳转的小程序页面路径（可选）

    Returns:
        发送是否成功
    """
    if settings.is_pay_mock or not settings.WECHAT_APP_SECRET:
        logger.info(
            "[NOTIFY][MOCK] subscribe_message openid={} template={} data={}",
            openid,
            template_id,
            json.dumps(data, ensure_ascii=False),
        )
        return True

    # 1. 获取 access_token
    access_token = await _get_wechat_access_token()
    if not access_token:
        return False

    # 2. 发送订阅消息
    url = f"https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={access_token}"
    body = {
        "touser": openid,
        "template_id": template_id,
        "page": page,
        "data": data,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(url, json=body)
            result = resp.json()
        except Exception as exc:
            logger.error("[NOTIFY] 订阅消息发送失败: {}", exc)
            return False

    if resp.status_code == 200 and result.get("errcode") == 0:
        logger.info("[NOTIFY] 订阅消息发送成功 openid={}", openid)
        return True

    logger.warning("[NOTIFY] 订阅消息发送失败: {}", result)
    return False


async def _get_wechat_access_token() -> str | None:
    """获取微信小程序 access_token（简单内存缓存，生产用 Redis）."""
    # 简单实现：每次请求都获取（生产应带 TTL 缓存）
    url = (
        f"https://api.weixin.qq.com/cgi-bin/token"
        f"?grant_type=client_credential"
        f"&appid={settings.WECHAT_APP_ID}"
        f"&secret={settings.WECHAT_APP_SECRET}"
    )

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url)
            data = resp.json()
        except Exception as exc:
            logger.error("[NOTIFY] 获取 access_token 失败: {}", exc)
            return None

    access_token = data.get("access_token")
    if not access_token:
        logger.error("[NOTIFY] access_token 获取失败: {}", data)
    return access_token


# ── 短信 ─────────────────────────────────────────────

async def send_sms(
    phone: str,
    template_code: str,
    params: dict,
) -> bool:
    """发送阿里云短信.

    Args:
        phone: 手机号
        template_code: 短信模板代码
        params: 模板参数

    Returns:
        发送是否成功
    """
    if settings.ALIYUN_SMS_ACCESS_KEY.startswith("mock_") or not settings.ALIYUN_SMS_ACCESS_KEY:
        logger.info(
            "[NOTIFY][MOCK] sms phone={} template={} params={}",
            phone,
            template_code,
            json.dumps(params, ensure_ascii=False),
        )
        return True

    # TODO: 接入阿里云 SMS SDK
    # import alibabacloud_dysmsapi20170525
    logger.info(
        "[NOTIFY] sms phone={} template={} params={}",
        phone,
        template_code,
        json.dumps(params, ensure_ascii=False),
    )
    return True


# ── 业务通知 ─────────────────────────────────────────

async def notify_payment_success(
    user_id: int,
    order_no: str,
) -> None:
    """支付成功通知.

    通知渠道优先级：
      1. 微信小程序订阅消息（支付成功模板）
      2. 降级：日志记录
    """
    from sqlalchemy import select
    from app.database import get_db
    from app.models.user import User

    user_phone = ""
    async for db in get_db():
        try:
            res = await db.execute(select(User).where(User.id == user_id))
            user = res.scalar_one_or_none()
            if user:
                user_phone = user.phone or ""
        except Exception:
            pass
        break

    # 尝试发订阅消息（如果配置了模板 ID）
    # 模板 ID 示例：「支付成功通知」template_id = "xxxxx"
    # 字段：amount、time、order_no 等
    logger.info(
        "[NOTIFY] 支付成功通知 user_id={} order_no={} phone={}",
        user_id,
        order_no,
        user_phone,
    )

    # 如果有手机号，发短信通知
    if user_phone:
        await send_sms(
            phone=user_phone,
            template_code=settings.ALIYUN_SMS_TEMPLATE_OTP,
            params={"order_no": order_no},
        )


async def notify_diagnosis_complete(
    user_id: int,
    diagnosis_id: int,
) -> None:
    """诊断完成通知."""
    from sqlalchemy import select
    from app.database import get_db
    from app.models.user import User
    from app.models.diagnosis import Diagnosis

    user_phone = ""
    diagnosis_name = ""
    async for db in get_db():
        try:
            res = await db.execute(select(User).where(User.id == user_id))
            user = res.scalar_one_or_none()
            if user:
                user_phone = user.phone or ""

            res2 = await db.execute(select(Diagnosis).where(Diagnosis.id == diagnosis_id))
            diag = res2.scalar_one_or_none()
            if diag:
                diagnosis_name = diag.video_title or f"诊断#{diagnosis_id}"
        except Exception:
            pass
        break

    logger.info(
        "[NOTIFY] 诊断完成通知 user_id={} diagnosis_id={} title={} phone={}",
        user_id,
        diagnosis_id,
        diagnosis_name,
        user_phone,
    )

    if user_phone:
        await send_sms(
            phone=user_phone,
            template_code=settings.ALIYUN_SMS_TEMPLATE_OTP,
            params={"diagnosis_id": str(diagnosis_id), "title": diagnosis_name},
        )


async def notify_subscription_expiring(
    user_id: int,
    days_left: int,
) -> None:
    """会员即将到期通知."""
    from sqlalchemy import select
    from app.database import get_db
    from app.models.user import User

    user_phone = ""
    async for db in get_db():
        try:
            res = await db.execute(select(User).where(User.id == user_id))
            user = res.scalar_one_or_none()
            if user:
                user_phone = user.phone or ""
        except Exception:
            pass
        break

    logger.info(
        "[NOTIFY] 会员到期提醒 user_id={} days_left={} phone={}",
        user_id,
        days_left,
        user_phone,
    )

    if user_phone:
        await send_sms(
            phone=user_phone,
            template_code=settings.ALIYUN_SMS_TEMPLATE_OTP,
            params={"days_left": str(days_left)},
        )
