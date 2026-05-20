"""支付回调 webhook."""
from __future__ import annotations

from fastapi import APIRouter, Request
from sqlalchemy import select

from app.database import get_db
from app.models.subscription import Order
from app.services import payment_service, subscription_service

router = APIRouter()


@router.post("/wechat/pay")
async def wechat_pay_callback(request: Request):
    payload = await request.json()
    ok, order_no = await payment_service.verify_wechat_callback(payload)
    if not ok or not order_no:
        return {"code": "FAIL", "message": "verify failed"}
    async for db in get_db():
        res = await db.execute(select(Order).where(Order.order_no == order_no))
        order = res.scalar_one_or_none()
        if order and order.payment_status != "paid":
            await subscription_service.activate_subscription(db, order)
            await db.commit()
        return {"code": "SUCCESS", "message": "OK"}
