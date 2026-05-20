"""统一异常 + 错误码."""
from __future__ import annotations

from fastapi import HTTPException, status


class BizException(HTTPException):
    """业务异常基类."""

    def __init__(self, code: str, message: str, http_status: int = 400):
        super().__init__(status_code=http_status, detail={"code": code, "message": message})


class NotFoundError(BizException):
    def __init__(self, resource: str = "resource"):
        super().__init__("NOT_FOUND", f"{resource} not found", http_status=status.HTTP_404_NOT_FOUND)


class UnauthorizedError(BizException):
    def __init__(self, message: str = "unauthorized"):
        super().__init__("UNAUTHORIZED", message, http_status=status.HTTP_401_UNAUTHORIZED)


class ForbiddenError(BizException):
    def __init__(self, message: str = "forbidden"):
        super().__init__("FORBIDDEN", message, http_status=status.HTTP_403_FORBIDDEN)


class QuotaExceededError(BizException):
    def __init__(self, quota_type: str):
        super().__init__("QUOTA_EXCEEDED", f"{quota_type} quota exceeded", http_status=429)


class PaymentError(BizException):
    def __init__(self, message: str):
        super().__init__("PAYMENT_ERROR", message, http_status=402)
