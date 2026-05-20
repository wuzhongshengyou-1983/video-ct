"""文件存储服务 · OSS (阿里云) / 本地磁盘双模式."""
from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from app.config import settings


# 尝试导入阿里云 OSS SDK
try:
    import oss2

    HAS_OSS = True
except ImportError:
    HAS_OSS = False
    logger.info("[Storage] oss2 not installed, OSS mode unavailable")


def _get_storage_path(filename: str) -> Path:
    """获取本地存储的完整路径."""
    return Path(settings.STORAGE_LOCAL_PATH) / filename


def _ensure_storage_dir() -> None:
    """确保本地存储目录存在."""
    Path(settings.STORAGE_LOCAL_PATH).mkdir(parents=True, exist_ok=True)


def _is_local_mode() -> bool:
    """判断是否为本地存储模式."""
    return settings.OSS_ENDPOINT.lower() == "local" or not settings.OSS_ENDPOINT


def _oss_client() -> Any | None:
    """创建 OSS 客户端，失败返回 None."""
    if not HAS_OSS:
        return None
    if _is_local_mode():
        return None
    try:
        auth = oss2.Auth(settings.OSS_ACCESS_KEY, settings.OSS_SECRET_KEY)
        endpoint = (
            f"https://oss-{settings.OSS_REGION}.aliyuncs.com"
            if not settings.OSS_ENDPOINT.startswith("http")
            else settings.OSS_ENDPOINT
        )
        return oss2.Bucket(auth, endpoint, settings.OSS_BUCKET)
    except Exception as exc:
        logger.warning(f"[Storage] 创建 OSS 客户端失败: {exc}")
        return None


async def upload_file(
    filename: str | None = None,
    content_bytes: bytes = b"",
    *,
    folder: str = "",
    public_read: bool = False,
) -> str:
    """上传文件 · 返回最终文件路径/key.

    Args:
        filename: 文件名（可选，不传则自动生成 UUID 文件名).
        content_bytes: 文件内容.
        folder: OSS 中的文件夹/前缀.
        public_read: 是否设为公共读（本地模式忽略).

    Returns:
        文件路径（本地为相对路径，OSS 为 object key).
    """
    if not filename:
        ext = ".bin"
        filename = f"{uuid.uuid4().hex}{ext}"

    key = f"{folder}/{filename}" if folder else filename

    if _is_local_mode():
        _ensure_storage_dir()
        filepath = _get_storage_path(key)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_bytes(content_bytes)
        logger.info(f"[Storage] 本地写入: {filepath} ({len(content_bytes)} bytes)")
        return key

    # OSS 模式
    bucket = _oss_client()
    if bucket is None:
        # OSS 不可用，降级本地
        logger.warning("[Storage] OSS 不可用，降级到本地存储")
        _ensure_storage_dir()
        filepath = _get_storage_path(key)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_bytes(content_bytes)
        return key

    headers = {}
    if public_read:
        headers["x-oss-object-acl"] = oss2.OBJECT_ACL_PUBLIC_READ

    bucket.put_object(key, content_bytes, headers=headers)
    logger.info(f"[Storage] OSS 上传: {key} ({len(content_bytes)} bytes)")
    return key


async def get_file_url(filename: str, *, expires_sec: int = 3600) -> str:
    """返回文件可访问 URL.

    Args:
        filename: 文件 path/key.
        expires_sec: OSS 签名 URL 过期时间（秒），本地模式忽略.

    Returns:
        可公开访问的文件 URL.
    """
    if _is_local_mode():
        # 本地模式：返回文件系统路径（实际应用建议用 static files middleware）
        filepath = _get_storage_path(filename)
        if filepath.exists():
            return f"{settings.API_BASE_URL}/static/uploads/{filename}"
        return ""

    bucket = _oss_client()
    if bucket is None:
        filepath = _get_storage_path(filename)
        if filepath.exists():
            return f"{settings.API_BASE_URL}/static/uploads/{filename}"
        return ""

    try:
        url = bucket.sign_url("GET", filename, expires_sec)
        return url
    except Exception as exc:
        logger.warning(f"[Storage] 获取 OSS URL 失败: {exc}")
        return f"{settings.API_BASE_URL}/static/uploads/{filename}"


async def delete_file(filename: str) -> bool:
    """删除文件 · 返回是否成功.

    Args:
        filename: 文件 path/key.

    Returns:
        是否删除成功（文件不存在也算成功).
    """
    if _is_local_mode():
        filepath = _get_storage_path(filename)
        if filepath.exists():
            filepath.unlink()
            logger.info(f"[Storage] 本地删除: {filepath}")
            return True
        logger.info(f"[Storage] 本地文件不存在，跳过删除: {filepath}")
        return True

    bucket = _oss_client()
    if bucket is None:
        filepath = _get_storage_path(filename)
        if filepath.exists():
            filepath.unlink()
        return True

    try:
        bucket.delete_object(filename)
        logger.info(f"[Storage] OSS 删除: {filename}")
        return True
    except Exception as exc:
        logger.warning(f"[Storage] OSS 删除失败: {exc}")
        return False


async def file_exists(filename: str) -> bool:
    """检查文件是否存在."""
    if _is_local_mode():
        return _get_storage_path(filename).exists()

    bucket = _oss_client()
    if bucket is None:
        return _get_storage_path(filename).exists()

    try:
        return bucket.object_exists(filename)
    except Exception:
        return False


async def generate_upload_key(user_id: int, original_filename: str, prefix: str = "uploads") -> str:
    """生成带时间戳的唯一上传 key.

    Args:
        user_id: 用户 ID.
        original_filename: 原始文件名.
        prefix: 前缀（如 uploads, avatars, videos).

    Returns:
        格式: {prefix}/{user_id}/{YYYY-MM}/{uuid}_{safe_name}
    """
    now = datetime.now()
    safe_name = Path(original_filename).name
    uid = uuid.uuid4().hex[:8]
    return f"{prefix}/{user_id}/{now:%Y-%m}/{uid}_{safe_name}"
