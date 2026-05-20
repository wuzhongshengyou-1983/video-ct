"""用户表."""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, String, Text, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, index=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String(120), unique=True, index=True, nullable=True)
    wechat_openid: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    nickname: Mapped[str] = mapped_column(String(64), default="新用户")
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="user")  # user / consultant / admin / partner
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_realname: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    profile: Mapped["UserProfile"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    track: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 细分赛道
    platform_main: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 抖音/快手/视频号/小红书
    follower_count: Mapped[int] = mapped_column(BigInteger, default=0)
    monetization_paths: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON 字符串
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    goals: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(back_populates="profile")
