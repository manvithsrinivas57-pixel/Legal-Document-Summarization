"""Audit trail tracker for tracking workflow stages, model provenance, and execution metrics."""

import datetime
import uuid
from typing import Any
from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    """Structured audit trail record representing a workflow step execution."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp_iso: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    stage_name: str
    model_identifier: str
    status: str  # "SUCCESS", "FAILED", "CHECKPOINT_MISSING", "SKIPPED", "WARNING"
    latency_seconds: float = 0.0
    details: dict[str, Any] = Field(default_factory=dict)


class AuditTrailTracker:
    """Thread-safe state manager for logging audit trail events throughout workflow execution."""

    def __init__(self):
        self.events: list[AuditEvent] = []

    def record_event(
        self,
        stage_name: str,
        model_identifier: str,
        status: str,
        latency_seconds: float = 0.0,
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Create and append an audit event."""
        event = AuditEvent(
            stage_name=stage_name,
            model_identifier=model_identifier,
            status=status,
            latency_seconds=latency_seconds,
            details=details or {},
        )
        self.events.append(event)
        return event

    def to_list(self) -> list[dict[str, Any]]:
        """Serialize audit events to a list of dicts."""
        return [e.model_dump() for e in self.events]

    def total_latency(self) -> float:
        """Calculate total cumulative latency across all recorded stages."""
        return round(sum(e.latency_seconds for e in self.events), 2)
