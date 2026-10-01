import hashlib
import json
import logging
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import AuditEvent
from app.services.gemini_client import GeminiError, GeminiRateLimited, analyze_action

logger = logging.getLogger("agentshield.ai")

CACHE_WINDOW = timedelta(hours=24)
PENDING_WINDOW = timedelta(minutes=2)
RATE_LIMIT_PAUSE_SECONDS = 60
MAX_CONCURRENT_ANALYSES = 3
PARAMETERS_PREVIEW_CHARS = 1500

_slots = threading.BoundedSemaphore(MAX_CONCURRENT_ANALYSES)
_paused_until = 0.0


def ai_enabled() -> bool:
    return bool(settings.gemini_api_key)


def build_fingerprint(
    *,
    tool: str,
    action: str,
    resource: str,
    decision: str,
    policy_decision: str,
    signal_codes: list[str],
    parameters: dict[str, Any],
) -> str:
    material = json.dumps(
        {
            "tool": tool,
            "action": action,
            "resource": resource,
            "decision": decision,
            "policy_decision": policy_decision,
            "signals": sorted(signal_codes),
            "parameters": parameters,
        },
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def prepare_analysis(db: Session, event: AuditEvent) -> bool:
    now = datetime.now(timezone.utc)
    reusable = db.scalar(
        select(AuditEvent.ai_analysis)
        .where(
            AuditEvent.analysis_fingerprint == event.analysis_fingerprint,
            AuditEvent.ai_status.in_(("completed", "cached")),
            AuditEvent.created_at >= now - CACHE_WINDOW,
        )
        .order_by(AuditEvent.created_at.desc())
        .limit(1)
    )
    if reusable is not None:
        event.ai_status = "cached"
        event.ai_analysis = reusable
        return False
    in_flight = db.scalar(
        select(AuditEvent.id)
        .where(
            AuditEvent.analysis_fingerprint == event.analysis_fingerprint,
            AuditEvent.ai_status == "pending",
            AuditEvent.created_at >= now - PENDING_WINDOW,
        )
        .limit(1)
    )
    return in_flight is None


def build_context(event: AuditEvent) -> dict[str, Any]:
    return {
        "tool": event.tool,
        "action": event.action,
        "resource": event.resource,
        "parameters_preview": json.dumps(event.parameters, default=str)[:PARAMETERS_PREVIEW_CHARS],
        "policy_decision": event.policy_decision,
        "final_decision": event.decision,
        "decision_reason_code": event.reason_code,
        "risk_score": event.risk_score,
        "risk_level": event.risk_level,
        "risk_signals": [
            {"code": signal["code"], "detail": signal["detail"]}
            for signal in event.risk_signals
        ],
    }


def _produce_analysis(event: AuditEvent) -> tuple[str, dict[str, Any] | None]:
    global _paused_until
    if not _slots.acquire(blocking=False):
        return "unavailable", None
    try:
        if time.monotonic() < _paused_until:
            return "unavailable", None
        try:
            analysis = analyze_action(build_context(event))
        except GeminiRateLimited:
            _paused_until = time.monotonic() + RATE_LIMIT_PAUSE_SECONDS
            logger.warning("Gemini rate limit reached, pausing AI analysis")
            return "unavailable", None
        except GeminiError as exc:
            logger.warning("Gemini analysis unavailable: %s", exc)
            return "unavailable", None
        return "completed", analysis.model_dump()
    finally:
        _slots.release()


def _store_result(
    db: Session, event: AuditEvent, status: str, analysis: dict[str, Any] | None
) -> None:
    db.execute(
        update(AuditEvent)
        .where(AuditEvent.id == event.id)
        .values(ai_status=status, ai_analysis=analysis)
    )
    if event.analysis_fingerprint:
        shared_status = "cached" if status == "completed" else status
        db.execute(
            update(AuditEvent)
            .where(
                AuditEvent.analysis_fingerprint == event.analysis_fingerprint,
                AuditEvent.ai_status == "pending",
                AuditEvent.id != event.id,
            )
            .values(ai_status=shared_status, ai_analysis=analysis)
        )
    db.commit()


def run_ai_analysis(event_id: uuid.UUID) -> None:
    with SessionLocal() as db:
        event = db.get(AuditEvent, event_id)
        if event is None or event.ai_status != "pending":
            return
        try:
            status, analysis = _produce_analysis(event)
        except Exception:
            logger.exception("AI analysis task failed")
            status, analysis = "unavailable", None
        _store_result(db, event, status, analysis)