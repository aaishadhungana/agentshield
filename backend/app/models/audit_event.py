import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_agent_id_created_at", "agent_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(unique=True, index=True)
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), index=True
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    tool: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(64))
    resource: Mapped[str] = mapped_column(String(128))
    parameters: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    decision: Mapped[str] = mapped_column(String(10), index=True)
    policy_decision: Mapped[str | None] = mapped_column(String(10))
    reason_code: Mapped[str] = mapped_column(String(50))
    reason: Mapped[str] = mapped_column(String(500))
    risk_score: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    risk_level: Mapped[str] = mapped_column(
        String(10), default="low", server_default="low"
    )
    risk_signals: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )
    ai_status: Mapped[str] = mapped_column(
        String(15), default="skipped", server_default="skipped"
    )
    ai_analysis: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB(none_as_null=True)
    )
    analysis_fingerprint: Mapped[str | None] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )