"""Unified intent recognition and entity extraction without downloaded resources."""
import json
import re
from pathlib import Path

from .context import PipelineContext, IntentCandidate
from .logic.booking import (detect_booking_intent, detect_cancel_intent,
                            extract_professor, parse_booking_request)
from .logic.data.course_aliases import COURSE_ALIAS_MAP

_DATA = Path(__file__).parent / "logic" / "data"
ACADEMIC_ENTITIES = json.loads((_DATA / "academic_entities.json").read_text(encoding="utf-8"))
BINDINGS = json.loads((_DATA / "binding_rules.json").read_text(encoding="utf-8"))["bindings"]
RULE_MAP = json.loads((_DATA / "intent_to_rule_map.json").read_text(encoding="utf-8"))
COURSE_INTENTS = [
    ("difficulty", r"\b(hard|difficult|difficulty|tough|rigorous)\b"),
    ("workload", r"\b(workload|pacing|busy|time.?consuming|how much work)\b"),
    ("tips", r"\b(tips?|advice|prepare|survive)\b"),
    ("sentiment", r"\b(worth it|worth taking|recommend(?:ed)?|opinion|thoughts?|reviews?|comments?|like it|sentiment|think of|feel about|say about)\b"),
]
_CODES = re.compile(r"(?<!\w)(?:" + "|".join(re.escape(c) for c in
                    sorted(set(COURSE_ALIAS_MAP.values()), key=lambda c: (-len(c), c))) + r")(?!\w)", re.I)


def _words(text: str) -> list[str]:
    text = re.sub(r"['’]s\b", "", text.lower())
    return [w for w in re.findall(r"[a-z0-9]+", text)
            if w not in {"a", "an", "the", "my", "of", "does", "is"}]


def _dictionary_entities(text: str) -> list[dict]:
    """Longest ordered n-grams win; preserve spans for action/target binding."""
    words = _words(text)
    matches = []
    for category, phrases in ACADEMIC_ENTITIES.items():
        if category == "COURSE_CODE":
            continue
        for phrase in phrases:
            needle = _words(phrase)
            for i in range(len(words) - len(needle) + 1):
                candidate = words[i:i + len(needle)]
                if needle and all(a == b or a.rstrip("s") == b.rstrip("s")
                                  for a, b in zip(candidate, needle)):
                    matches.append({"category": category, "entity": phrase,
                                    "start": i, "end": i + len(needle)})
    accepted, occupied = [], set()
    for item in sorted(matches, key=lambda m: (-(m["end"] - m["start"]), m["start"], m["category"])):
        span = set(range(item["start"], item["end"]))
        if not span & occupied:
            accepted.append(item)
            occupied |= span
    return sorted(accepted, key=lambda m: m["start"])


def interpret(ctx: PipelineContext) -> PipelineContext:
    text = ctx.normalized_text.lower()
    raw = ctx.raw_text
    codes = list(dict.fromkeys(m[0].upper() for m in _CODES.finditer(ctx.normalized_text)))
    matches = _dictionary_entities(text)
    categories = {m["category"] for m in matches}
    advisor = extract_professor(raw)
    details, errors, notes = parse_booking_request(raw)
    ctx.entities.update(course_codes=codes, target=codes[0] if codes else advisor,
                        rule_id=None, action=None, advisor=advisor, date=None, time=None,
                        modality=None, place=None, topic=None, notes=None,
                        booking_errors=errors, booking_notes=notes, academic_entities=matches)
    ctx.entities.update(details)
    mentioned = re.findall(r"(?<![\w/])(?:CB|CC|LBY|MTH|STT|THS)[A-Z0-9/-]+(?!\w)", ctx.normalized_text.upper())
    ctx.entities["unknown_courses"] = [code for code in mentioned if code.lower() not in COURSE_ALIAS_MAP]
    # Crisis phrases remain upstream even when a course intent is also present.
    crisis = bool(re.search(r"\b(suicid\w*|self[- ]harm|kill myself|hurt myself|end myself|want to die|don't want to live|do not want to live)\b", text))
    distress = "ACADEMIC_DISTRESS" in categories
    bare_cancel = bool(re.fullmatch(
        r"(?:please )?(?:cancel(?: it)?|stop|never mind|nevermind|abort|"
        r"(?:cancel|stop|forget) (?:this|the|current) (?:check|flow|request))[.! ]*", text))
    cancel_booking = detect_cancel_intent(raw)
    negated_booking = bool(re.search(r"\b(?:don't|do not|never)\s+(?:book|schedule|reserve|cancel)\b", text))
    ctx.control_flags.update(crisis=crisis, academic_distress=distress,
                             negated_booking=negated_booking,
                             cancel_flow=bare_cancel and bool(ctx.session_state.get("active_workflow")
                                 or ctx.session_state.get("clarification_options")
                                 or ctx.session_state.get("pending_intent")
                                 or ctx.session_state.get("suspended_workflows")))
    greeting = re.fullmatch(r"(?:hi|hello|hey|greetings|hola|kamusta)(?: archi)?[!. ]*", raw.lower().strip())
    thanks = re.fullmatch(r"(?:thanks|thank you|salamat)(?: archi)?[!. ]*", raw.lower().strip())
    intent = None
    if greeting:
        intent = "greeting"
    elif thanks:
        intent = "thanks"
    elif negated_booking:
        intent = "out_of_scope"
    elif cancel_booking and not negated_booking:
        intent = "cancel_consultation"
    elif detect_booking_intent(raw) and not negated_booking:
        intent = "book_consultation"
    elif re.search(r"\b(prerequisites?|pre[- ]?reqs?|co[- ]?requisites?)\b", text):
        intent = "prerequisites"
    elif (re.search(r"\b(eligible|eligibility|qualified|allowed)\b|\bcan i (take|enroll)\b", text)
          and (codes or not (categories & (RULE_MAP.keys() - {"RETENTION_TERM"})))):
        intent = "eligibility"
    elif re.search(r"\b(offered|offerings?|available terms?)\b", text) and codes:
        intent = "offerings"
    elif "ACTION_UPDATE" in categories and "FLOWCHART_TERM" in categories:
        intent = "FLOWCHART_UPDATE"
    else:
        # Bind actions to their domain targets before handbook or survey matching.
        for rule in BINDINGS:
            action = rule["action_category"]
            target = codes[0] if codes and rule["target_category"] == "COURSE_CODE" else advisor if rule["target_category"] == "PERSON" else None
            if action in categories and target:
                intent = "ACTION_ADVISE" if action == "ACTION_CANCEL" and codes else action
                ctx.entities.update(target=target, action="drop" if action == "ACTION_CANCEL" else "underload")
                break
        if not intent:
            intent = next((i for i in ("GPA_CALCULATE", "GPA_UNDERSTAND", "GPA_LOW_CONCERN", "GPA_IMPROVE", "STATUS_CHECK") if i in categories), None)
        if not intent and "ACTION_ADVISE" in categories:
            intent = "ACTION_ADVISE"
            ctx.entities["action"] = "underload"
        if intent == "STATUS_CHECK" and not ctx.entities["target"]:
            ctx.entities["target"] = "enrollment"
        if not intent:
            for match in sorted(matches, key=lambda m: (-(m["end"] - m["start"]), m["start"])):
                if match["category"] in RULE_MAP:
                    ctx.entities["rule_id"] = RULE_MAP[match["category"]]
                    intent = "handbook"
                    break
        if not intent:
            intent = next((i for i, pattern in COURSE_INTENTS if re.search(pattern, text)), None)
    if not intent and codes:
        intent = "overview"
    ctx.intent = intent or "out_of_scope"
    ctx.confidence = 0.0 if ctx.intent == "out_of_scope" else 1.0
    ctx.candidates = _collect_candidates(ctx)
    return ctx


_ACADEMIC_PATTERNS = (
    ("prerequisites", r"\b(prerequisites?|pre[- ]?reqs?|co[- ]?requisites?)\b"),
    ("eligibility", r"\b(eligible|eligibility|qualified|allowed to take)\b|\bcan i (take|enroll)\b"),
    ("offerings", r"\b(offered|offerings?|available terms?)\b"),
)
INTENT_LABELS = {
    "book_consultation": "book a consultation", "cancel_consultation": "cancel a consultation draft",
    "consultation_policy": "consultation policy", "handbook": "handbook policy",
    "eligibility": "eligibility", "prerequisites": "prerequisites", "offerings": "course offerings",
    **{intent: intent for intent, _ in COURSE_INTENTS},
}


def _collect_candidates(ctx: PipelineContext) -> list[IntentCandidate]:
    """Keep independent requests; booking topics are not separate commands."""
    if ctx.control_flags.get("negated_booking") or ctx.intent in ("greeting", "thanks"):
        return []
    candidates = []
    clauses = re.split(r"\s+(?:and(?: also)?|also)\s+|;\s*", ctx.normalized_text, flags=re.I)
    for clause in clauses:
        codes = list(dict.fromkeys(m[0].upper() for m in _CODES.finditer(clause)))
        entities = dict(ctx.entities)
        # A sole course applies to both 'difficulty and workload of CBOPESY'.
        entities["course_codes"] = codes or (ctx.entities["course_codes"] if len(ctx.entities["course_codes"]) == 1 else [])
        if entities["course_codes"]:
            entities["target"] = entities["course_codes"][0]
        consultation = bool(re.search(r"\b(consultations?|appointments?|meetings?|bookings?|drafts?)\b", clause, re.I))
        policy = consultation and bool(re.search(r"\b(policy|rules|how (?:does|do|can|to)|what happens)\b", clause, re.I))
        booking = detect_booking_intent(clause) or detect_cancel_intent(clause)
        if policy:
            intents = ["consultation_policy"]
        elif booking:
            intents = ["cancel_consultation" if detect_cancel_intent(clause) else "book_consultation"]
        else:
            intents = [i for i, pattern in _ACADEMIC_PATTERNS if re.search(pattern, clause, re.I)]
            if ctx.intent == "handbook" and not codes:
                intents = []  # 'Can I enroll with an overload?' is a policy question.
            intents.extend(i for i, pattern in COURSE_INTENTS if re.search(pattern, clause, re.I)
                           and not (i == "tips" and intents))
            categories = {m["category"] for m in _dictionary_entities(clause)}
            academic = next((i for i in ("GPA_CALCULATE", "GPA_UNDERSTAND", "GPA_LOW_CONCERN",
                                       "GPA_IMPROVE", "STATUS_CHECK") if i in categories), None)
            if academic:
                intents.append(academic)
            if "ACTION_UPDATE" in categories and "FLOWCHART_TERM" in categories:
                intents.append("FLOWCHART_UPDATE")
        for intent in intents:
            candidate = IntentCandidate(intent, INTENT_LABELS.get(intent, intent.lower().replace("_", " ")), entities.copy())
            if not any(c.intent == intent and c.entities == candidate.entities for c in candidates):
                candidates.append(candidate)
    if len(candidates) == 1 and candidates[0].intent not in ("book_consultation", "cancel_consultation", "consultation_policy"):
        candidates[0].entities["course_codes"] = ctx.entities["course_codes"]
    if not candidates and ctx.intent not in ("overview", "out_of_scope", "greeting", "thanks"):
        candidates.append(IntentCandidate(ctx.intent, INTENT_LABELS.get(ctx.intent, ctx.intent.lower().replace("_", " ")), dict(ctx.entities)))
    return candidates
