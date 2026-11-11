"""Typed contracts for a single, side-effect controlled conversation turn."""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Literal

Status = Literal['answered', 'needs_input', 'needs_clarification', 'draft_created', 'cancelled', 'unsupported', 'error']

@dataclass
class MessageRequest:
    chat_id: str
    message_id: str
    text: str
    message_type: str = 'text'
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    timezone: str = 'Asia/Manila'

@dataclass
class IntentCandidate:
    group: str
    intent: str
    entities: dict = field(default_factory=dict)
    evidence: list = field(default_factory=list)
    specificity: int = 1
    missing_fields: list = field(default_factory=list)

@dataclass
class ConversationContext:
    schema_version: int = 1
    active_group: str | None = None
    active_intent: str | None = None
    slots: dict = field(default_factory=dict)
    pending_question: str | None = None
    clarification_options: list = field(default_factory=list)

@dataclass
class Interpretation:
    original_text: str
    tokens: list
    entity_spans: list
    negation: bool
    candidates: list
    distress_signals: list
    request: MessageRequest

@dataclass
class RouteDecision:
    group: str
    intent: str
    rule_id: str
    entities: dict = field(default_factory=dict)
    clarification_required: bool = False

@dataclass
class HandlerResult:
    status: Status
    response_data: dict
    context: dict
    action_request: dict | None = None

@dataclass
class TurnResult:
    reply: str
    context: dict
    navigation: str | None = None
    diagnostics: dict = field(default_factory=dict)
