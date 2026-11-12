"""Public orchestration API for the academic assistant."""
from copy import deepcopy
from dataclasses import replace
import logging

from .context import PipelineContext, TurnResult, ensure_session_state
from .preprocessor import preprocess
from .interpreter import interpret
from .routing.router import Router

logger = logging.getLogger(__name__)


class NLPPipeline:
    def __init__(self, db_client=None, booking_service=None):
        self.router = Router(db_client, booking_service)

    def process_result(self, user_input: str, session_state: dict | None = None,
                       *, message_id: str | None = None) -> TurnResult:
        """Process once per message ID within a chat; commit state after success.

        IDs must be unique per submission, not derived from message text. Cached
        replies never re-emit booking events. The cache lives for the chat session;
        external services must supply their own durable idempotency if needed.
        """
        session = ensure_session_state(session_state)
        cache = session["processed_results"]
        if message_id is not None and message_id in cache:
            previous = cache[message_id]
            if previous["text"] != user_input:
                raise ValueError("A message ID cannot be reused with different text.")
            return replace(deepcopy(previous["result"]), duplicate=True)
        working = deepcopy({key: value for key, value in session.items() if key != "processed_results"})
        before = (working.get("active_workflow"), working.get("pending_slot"))
        ctx = preprocess(user_input or "", working)
        try:
            reply = self.router.dispatch(interpret(ctx))
        except Exception:
            logger.exception("Pipeline handler failed: route=%s group=%s", ctx.route_id, ctx.group)
            ctx.status = "error"
            reply = "I couldn't complete that request. Your previous conversation state has been kept; please try again."
        else:
            session.clear()
            session.update({key: value for key, value in working.items() if key != "processed_results"})
            session["processed_results"] = cache
        diagnostics = {
            "rule_id": ctx.route_id, "group": ctx.group, "intent": ctx.intent,
            "candidates": [c.intent for c in ctx.candidates], "status": ctx.status,
            "workflow_before": before[0], "slot_before": before[1],
            "workflow_after": session.get("active_workflow"), "slot_after": session.get("pending_slot"),
        }
        result = TurnResult(reply, ctx.status, diagnostics)
        session["last_diagnostics"] = diagnostics.copy()
        if message_id is not None:
            cache[message_id] = {"text": user_input, "result": deepcopy(result)}
        logger.info("Pipeline turn: %s", diagnostics)
        return result

    def process_turn(self, user_input: str, session_state: dict | None = None,
                     *, message_id: str | None = None) -> str:
        return self.process_result(user_input, session_state, message_id=message_id).reply


__all__ = ["NLPPipeline", "PipelineContext", "TurnResult", "preprocess", "interpret", "Router"]
