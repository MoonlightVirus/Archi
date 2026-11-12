"""Per-chat pipeline values and workflow state."""
from dataclasses import dataclass, field
from typing import Any


def ensure_session_state(session: dict | None = None) -> dict:
    session = session if session is not None else {}
    for key, default in (("active_workflow", None), ("pending_slot", None),
                         ("slots", {}), ("completed_booking", None),
                         ("clarification_options", []), ("last_course", None),
                         ("pending_intent", None), ("processed_results", {})):
        session.setdefault(key, default)
    return session


def clear_workflow(session: dict) -> None:
    session.update(active_workflow=None, pending_slot=None, slots={})


@dataclass
class IntentCandidate:
    intent: str
    label: str
    entities: dict[str, Any] = field(default_factory=dict)


@dataclass
class TurnResult:
    reply: str
    status: str
    diagnostics: dict[str, Any] = field(default_factory=dict)
    duplicate: bool = False


@dataclass
class PipelineContext:
    raw_text: str
    normalized_text: str = ""
    intent: str | None = None
    confidence: float = 0.0
    entities: dict[str, Any] = field(default_factory=dict)
    control_flags: dict[str, Any] = field(default_factory=dict)
    session_state: dict[str, Any] = field(default_factory=dict)
    candidates: list[IntentCandidate] = field(default_factory=list)
    route_id: str = "R00_INPUT"
    group: str = "Fallback"
    status: str = "answered"
