"""Services 层 · 业务逻辑 + 外部服务集成."""
from app.services.auth_service import send_otp, verify_otp, login_or_register_by_phone, issue_token
from app.services.subscription_service import (
    create_order,
    activate_subscription,
    get_active_subscription,
    get_user_tier,
    gen_order_no,
)
from app.services.payment_service import (
    create_jsapi_order,
    create_h5_order,
    query_order,
    verify_wechat_callback,
    create_wechat_pay,
    refresh_platform_certificates,
)
from app.services.notification import (  # noqa: F401
    send_subscribe_message,
    send_sms,
    notify_diagnosis_complete,
    notify_payment_success,
    notify_subscription_expiring,
)
from app.services.diagnosis_service import DiagnosisService
from app.services.llm_router import llm_router, LLMRouter, LLMResponse
from app.services.ocr_asr import extract_text_from_image, transcribe_audio, extract_video_info
from app.services.storage import upload_file, get_file_url, delete_file, file_exists, generate_upload_key
from app.services.task_queue import TaskQueue

__all__ = [
    # auth
    "send_otp",
    "verify_otp",
    "login_or_register_by_phone",
    "issue_token",
    # subscription
    "create_order",
    "activate_subscription",
    "get_active_subscription",
    "get_user_tier",
    "gen_order_no",
    # payment
    "create_jsapi_order",
    "create_h5_order",
    "query_order",
    "verify_wechat_callback",
    "create_wechat_pay",
    "refresh_platform_certificates",
    # notification
    "send_subscribe_message",
    "send_sms",
    "notify_diagnosis_complete",
    "notify_payment_success",
    "notify_subscription_expiring",
    # other services
    "DiagnosisService",
    "llm_router",
    "LLMRouter",
    "LLMResponse",
    "extract_text_from_image",
    "transcribe_audio",
    "extract_video_info",
    "upload_file",
    "get_file_url",
    "delete_file",
    "file_exists",
    "generate_upload_key",
    "TaskQueue",
]
