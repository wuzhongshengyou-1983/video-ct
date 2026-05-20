"""支付服务 · 微信支付 mock 实现（真实接入需商户号）."""
from __future__ import annotations

from loguru import logger

from app.config import settings
from app.models.subscription import Order


async def create_wechat_pay(order: Order) -> dict:
    """创建微信支付 · 返回前端调起所需参数."""
    if settings.WECHAT_PAY_MCH_ID and not settings.WECHAT_PAY_MCH_ID.startswith("mock_"):
        # TODO: 真实 wechatpayv3 SDK 调用
        logger.warning("生产微信支付未实现，请接入 wechatpayv3")
        return {"mock": True, "order_no": order.order_no}

    # mock 模式：返回伪二维码 URL
    return {
        "order_no": order.order_no,
        "pay_url": f"weixin://wxpay/bizpayurl?pr=mock_{order.order_no}",
        "qr_code": f"https://api.qrserver.com/v1/create-qr-code/?data={order.order_no}",
        "mock": True,
    }


async def verify_wechat_callback(payload: dict) -> tuple[bool, str | None]:
    """验签 + 返回订单号. mock 模式直接通过."""
    if payload.get("mock"):
        return True, payload.get("order_no")
    # TODO: 真实验签
    return False, None
