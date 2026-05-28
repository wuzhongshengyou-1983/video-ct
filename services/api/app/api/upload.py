"""文件上传路由."""
from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile

from app.deps import CurrentUser

router = APIRouter()

# 上传目录：本地开发 parents[4]=repo_root，容器内 parents[2]=/app
try:
    UPLOAD_DIR = Path(__file__).resolve().parents[4] / "storage" / "uploads" / "avatars"
except IndexError:
    UPLOAD_DIR = Path(__file__).resolve().parents[2] / "storage" / "uploads" / "avatars"
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE = 2 * 1024 * 1024  # 2MB


@router.post("/avatar")
async def upload_avatar(file: UploadFile, _user: CurrentUser):
    """上传用户头像，返回访问 URL"""
    if file.content_type not in ALLOWED_TYPES:
        return {"ok": False, "message": "仅支持 jpeg/png/webp 格式"}, 400

    content = await file.read()
    if len(content) > MAX_SIZE:
        return {"ok": False, "message": "图片大小不能超过 2MB"}, 400

    # 确保目录存在
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # 生成唯一文件名
    ext = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = UPLOAD_DIR / filename

    with open(filepath, "wb") as f:
        f.write(content)

    url = f"/static/uploads/avatars/{filename}"
    return {"ok": True, "url": url}
