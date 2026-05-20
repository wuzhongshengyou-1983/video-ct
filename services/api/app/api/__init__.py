"""路由总入口."""
from fastapi import APIRouter

from app.api import (
    auth, users, subscription, diagnosis, benchmark,
    archive, persona, positioning, referrer, ai, admin, webhook, analytics, wechat, upload,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(subscription.router, prefix="/subscriptions", tags=["subscription"])
api_router.include_router(diagnosis.router, prefix="/diagnoses", tags=["diagnosis"])
api_router.include_router(benchmark.router, prefix="/benchmarks", tags=["benchmark"])
api_router.include_router(archive.router, prefix="/archives", tags=["archive"])
api_router.include_router(persona.router, prefix="/personas", tags=["persona"])
api_router.include_router(positioning.router, prefix="/positionings", tags=["positioning"])
api_router.include_router(referrer.router, prefix="/referrers", tags=["referrer"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(webhook.router, prefix="/webhooks", tags=["webhook"])
api_router.include_router(analytics.router, tags=["analytics"])
api_router.include_router(wechat.router, prefix="/wechat", tags=["wechat"])
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
