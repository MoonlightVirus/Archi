"""Resolve intent ambiguity and follow-ups before invoking domain behavior."""
from copy import deepcopy
from functools import partial
import re

from pipeline.context import PipelineContext, clear_workflow
from pipeline.logic.booking import process_booking
from pipeline.logic.fallback import resolve_fallback
from pipeline.logic.data.course_aliases import suggest_courses
from pipeline.logic.retrieval import query_domain, INTENT_RESPONSES
from .support import support_response

COURSE_INTENTS = {"difficulty", "workload", "tips", "sentiment", "overview",
                  "prerequisites", "eligibility", "offerings"}
WORKFLOW_INTENTS = {"Booking": "book_consultation", "Academic_Eligibility": "eligibility"}
WORKFLOW_KEYS = ("active_workflow", "pending_slot", "slots", "booking_errors")


def _question(text):
    return bool(re.search(r"\b(what|why|how|policy|prerequisites?|eligible)\b|\?", text, re.I))


def _selection(text, options):
    text = text.strip().lower().rstrip(".! ")
    if text.isdigit() and 1 <= int(text) <= len(options):
        return options[int(text) - 1]
    matches = [c for c in options if text in (c.intent.lower(), c.label.lower())]
    return matches[0] if len(matches) == 1 else None


def _course_slot_answer(ctx):
    session = ctx.session_state
    if session.get("active_workflow") != "Academic_Eligibility" or session.get("pending_slot") not in ("passed_courses", "taken_courses"):
        return False
    text = ctx.normalized_text
    if any(c.intent != "ACTION_FAIL" for c in ctx.candidates):
        return False
    commands = re.search(r"\b(book|schedule|cancel|prerequisites?|eligibility|difficulty|workload|tips|sentiment|offered)\b", text, re.I)
    return not _question(text) and not commands and bool(
        ctx.entities.get("course_codes") or ctx.entities.get("unknown_courses")
        or re.fullmatch(r"(?:none|no(?: other)? courses|nothing|no)[.! ]*", text, re.I))


def _booking_slot_answer(ctx):
    if ctx.session_state.get("active_workflow") != "Booking" or _question(ctx.normalized_text):
        return False
    # '9 AM online about my GPA' supplies booking details, not a GPA request.
    details = any(ctx.entities.get(key) is not None for key in ("advisor", "date", "time", "modality", "place"))
    topic_only = not ctx.candidates or bool(re.search(r"\b(about|regarding|to discuss)\b", ctx.normalized_text, re.I))
    control = any(c.intent in ("cancel_consultation", "consultation_policy") for c in ctx.candidates)
    return details and topic_only and not control


class Router:
    def __init__(self, db_client=None, booking_service=None):
        self.registry = {
            "Course": partial(query_domain, source="course"),
            "Academic": partial(query_domain, source="academic"),
            "Booking": partial(process_booking, booking_service=booking_service),
            "Fallback": resolve_fallback,
        }

    def _run(self, ctx, group, rule):
        ctx.group, ctx.route_id = group, rule
        return self.registry[group](ctx)

    def _clarify(self, ctx, options):
        ctx.session_state["clarification_options"] = deepcopy(options)
        ctx.route_id, ctx.group, ctx.status = "R04_CLARIFY", "Control", "needs_clarification"
        lines = [f"{n}. {c.label}" + (" — " + ", ".join(c.entities["course_codes"])
                 if c.entities.get("course_codes") else "") for n, c in enumerate(options, 1)]
        return "I found more than one request. Which should I handle first?\n" + "\n".join(lines)

    def _workflow(self, ctx, rule="R05_FOLLOWUP"):
        workflow = ctx.session_state["active_workflow"]
        ctx.intent = WORKFLOW_INTENTS[workflow]
        return self._run(ctx, "Booking" if workflow == "Booking" else "Academic", rule)

    def _activate(self, ctx, workflow):
        session = ctx.session_state
        current = session.get("active_workflow")
        if current and current != workflow:
            session.setdefault("suspended_workflows", {})[current] = {
                key: deepcopy(session.get(key)) for key in WORKFLOW_KEYS
            }
            clear_workflow(session)
            session.pop("booking_errors", None)

    def _resume(self, ctx):
        session = ctx.session_state
        saved = session.get("suspended_workflows", {})
        if saved:
            name = next(reversed(saved))
            snapshot = saved.pop(name)
            self._activate(ctx, name)
            session.update(snapshot)
            if session["slots"].get("target_course"):
                session["last_course"] = session["slots"]["target_course"]
        if session.get("active_workflow"):
            ctx.control_flags["repeat_prompt"] = True
            return self._workflow(ctx, "R05_RESUME")
        ctx.route_id = "R05_NO_WORKFLOW"
        return "There is no unfinished request to resume. What would you like help with?"

    def _course_context(self, ctx):
        session = ctx.session_state
        codes = ctx.entities.get("course_codes", [])
        if ctx.entities.get("unknown_courses"):
            ctx.route_id, ctx.group, ctx.status = "R04_UNKNOWN_COURSE", "Control", "needs_input"
            session["pending_intent"] = ctx.intent
            suggestions = suggest_courses(" ".join(ctx.entities["unknown_courses"]))
            session["pending_course_choices"] = suggestions
            suffix = " Did you mean: " + ", ".join(suggestions) + "?" if suggestions else " Please correct them."
            return "I couldn't recognize these course codes: " + ", ".join(ctx.entities["unknown_courses"]) + "." + suffix
        if not codes and session.get("last_course"):
            codes = [session["last_course"]]
            ctx.entities.update(course_codes=codes, target=codes[0])
        if not codes or len(codes) > 1:
            session["pending_intent"] = ctx.intent
            session["pending_entities"] = deepcopy(ctx.entities)
            suggestions = codes or suggest_courses(ctx.raw_text)
            session["pending_course_choices"] = suggestions
            ctx.route_id, ctx.group, ctx.status = "R04_COURSE", "Control", "needs_input"
            if codes:
                return "Please choose one course: " + ", ".join(codes)
            suffix = " Did you mean: " + ", ".join(suggestions) + "?" if suggestions else ""
            return "Which course do you mean? Please provide its code or full name." + suffix
        session["last_course"] = codes[0]
        return None

    def _explicit(self, ctx, rule="R06_EXPLICIT"):
        session = ctx.session_state
        session["pending_intent"] = None
        session.pop("pending_entities", None)
        session.pop("pending_course_choices", None)
        if ctx.intent in COURSE_INTENTS:
            prompt = self._course_context(ctx)
            if prompt:
                return prompt
        if ctx.intent == "consultation_policy":
            ctx.route_id, ctx.group, ctx.status = rule, "Academic", "unsupported"
            return "I don't have a verified consultation cancellation policy. Please check with your advisor. No draft has been changed."
        if ctx.intent in ("book_consultation", "cancel_consultation"):
            session.get("suspended_workflows", {}).pop("Booking", None)
            self._activate(ctx, "Booking")
            return self._run(ctx, "Booking", rule)
        if ctx.intent == "eligibility":
            session.get("suspended_workflows", {}).pop("Academic_Eligibility", None)
            self._activate(ctx, "Academic_Eligibility")
            # Explicit requests start a new check; slot answers use _workflow.
            clear_workflow(session)
        if ctx.intent in {"difficulty", "workload", "tips", "sentiment", "overview"}:
            return self._run(ctx, "Course", rule)
        if ctx.intent in {"prerequisites", "eligibility", "handbook", "offerings"} or ctx.intent in INTENT_RESPONSES:
            return self._run(ctx, "Academic", rule)
        return self._run(ctx, "Fallback", "R08_FALLBACK")

    def dispatch(self, ctx: PipelineContext) -> str:
        session = ctx.session_state
        text = ctx.normalized_text.strip()
        if not text:
            ctx.status = "unsupported"
            return self._run(ctx, "Fallback", "R01_EMPTY")
        if ctx.control_flags.get("crisis") or ctx.control_flags.get("academic_distress"):
            clear_workflow(session)
            session.update(completed_booking=None, clarification_options=[], pending_intent=None,
                           suspended_workflows={})
            session.pop("booking_errors", None)
            ctx.route_id, ctx.group = "R02_SUPPORT", "Support"
            return support_response(ctx)
        if ctx.control_flags.get("cancel_flow"):
            booking = session.get("active_workflow") == "Booking"
            clear_workflow(session)
            session.update(completed_booking=None, clarification_options=[], pending_intent=None,
                           suspended_workflows={})
            session.pop("booking_errors", None)
            if booking:
                session["cancelled_booking"] = {"advisor": None}
            ctx.route_id, ctx.group, ctx.status = "R03_CANCEL", "Control", "cancelled"
            return "I've cancelled the unfinished request. What would you like help with next?"
        if ctx.control_flags.get("negated_booking"):
            ctx.route_id, ctx.group = "R03_NEGATED", "Control"
            return "I haven't changed your consultation request. Tell me what you'd like to do next."
        options = session.get("clarification_options", [])
        if options:
            chosen = _selection(text, options)
            if chosen:
                session["clarification_options"] = []
                ctx.intent, ctx.entities = chosen.intent, deepcopy(chosen.entities)
                return self._explicit(ctx, "R04_SELECTED")
            if not ctx.candidates:
                return self._clarify(ctx, options)
            session["clarification_options"] = []
        if re.fullmatch(r"(?:resume|continue)(?: (?:the |my )?(?:previous |earlier )?(?:request|check|booking))?[.! ]*", text, re.I):
            return self._resume(ctx)
        pending_intent = session.get("pending_intent")
        if pending_intent and not ctx.candidates:
            codes = ctx.entities.get("course_codes", [])
            choices = session.get("pending_course_choices", [])
            if choices and text.isdigit() and 1 <= int(text) <= len(choices):
                codes = [choices[int(text) - 1]]
            if len(codes) == 1:
                ctx.intent = pending_intent
                ctx.entities.update(session.get("pending_entities", {}))
                ctx.entities.update(course_codes=codes, target=codes[0])
                return self._explicit(ctx, "R04_COURSE_SELECTED")
            ctx.route_id, ctx.group, ctx.status = "R04_COURSE", "Control", "needs_input"
            return "Please provide one course code or full name."
        if _course_slot_answer(ctx) or _booking_slot_answer(ctx):
            return self._workflow(ctx, "R05_VALID_SLOT")
        if len(ctx.candidates) > 1:
            return self._clarify(ctx, ctx.candidates)
        if ctx.candidates:
            candidate = ctx.candidates[0]
            ctx.intent, ctx.entities = candidate.intent, candidate.entities
            return self._explicit(ctx)
        if ctx.intent in ("greeting", "thanks"):
            return self._run(ctx, "Fallback", "R07_CONVERSATION")
        if session.get("active_workflow"):
            if _question(text):
                ctx.status = "unsupported"
                return self._run(ctx, "Fallback", "R08_UNRECOGNIZED_QUESTION")
            return self._workflow(ctx)
        if ctx.intent == "overview":
            return self._explicit(ctx, "R06_COURSE_OVERVIEW")
        ctx.status = "unsupported"
        return self._run(ctx, "Fallback", "R08_FALLBACK")


def dispatch(ctx: PipelineContext) -> str:
    return Router().dispatch(ctx)
