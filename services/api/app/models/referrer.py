"""品牌分享官体系."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ReferrerLink(Base):
    """分享官归因记录."""
    __tablename__ = "referrer_links"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    inviter_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    invitee_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True, index=True)
    link_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    first_paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reward_amount_cny: Mapped[int] = mapped_column(Integer, default=0)
    reward_status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReferrerLevel(Base):
    """每位分享官的等级状态."""
    __tablename__ = "referrer_levels"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    level: Mapped[str] = mapped_column(String(10), default="bronze")  # bronze / silver / gold / diamond
    total_valid_referrals: Mapped[int] = mapped_column(Integer, default=0)
    total_rewards_cny: Mapped[int] = mapped_column(Integer, default=0)
    activated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    level_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RewardAccount(Base):
    """通用奖励账户：现金余额 + 抵扣余额 + 诊断券."""
    __tablename__ = "reward_accounts"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    cash_balance_cny: Mapped[int] = mapped_column(Integer, default=0)
    deduction_balance_cny: Mapped[int] = mapped_column(Integer, default=0)
    ticket_balance: Mapped[int] = mapped_column(Integer, default=0)  # 诊断券数量
    total_earned_cny: Mapped[int] = mapped_column(Integer, default=0)
    total_withdrawn_cny: Mapped[int] = mapped_column(Integer, default=0)
    total_deducted_cny: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RewardTransaction(Base):
    """奖励账户流水."""
    __tablename__ = "reward_transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    txn_type: Mapped[str] = mapped_column(String(20))  # earn / withdraw / deduct / refund / adjust
    amount_cny: Mapped[int] = mapped_column(Integer)
    balance_after_cny: Mapped[int] = mapped_column(Integer)
    related_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
