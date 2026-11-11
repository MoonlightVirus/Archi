import re
from .models import RouteDecision

def _decision(group, intent, rule, **entities):
    return RouteDecision(group, intent, rule, entities)


def _clarification(t, context):
    options = context.get('clarification_options', [])
    text = t.casefold()
    selected = [
        option for option in options
        if text in {
            option.get('intent', '').casefold(),
            option.get('group', '').casefold(),
            option.get('label', '').casefold(),
        }
    ]
    if len(selected) != 1:
        return None
    option = selected[0]
    return _decision(
        option['group'], option['intent'], 'R04_CLARIFICATION',
        **option.get('entities', {})
    )


def _has_question_language(text):
    return re.search(
        r"\b(what|why|how|policy|prerequisites?|eligible)\b|\?",
        text,
        re.I,
    )


def _is_course_slot_answer(text, item, pending):
    return (
        pending in ('passed_courses', 'taken_courses')
        and (item.entity_spans or re.search(r"\b(none|no|not|didn't)\b", text, re.I))
        and not _has_question_language(text)
    )


def _is_slot_answer(t, item, pending):
    return _is_course_slot_answer(t, item, pending) or (
        pending == 'term'
        and re.fullmatch(r'(?:term\s*)?[1-3][.! ]*', t, re.I)
    )


def _explicit_candidate(item):
    if not item.candidates:
        return None
    best = max(candidate.specificity for candidate in item.candidates)
    candidates = [
        candidate for candidate in item.candidates
        if candidate.specificity == best
    ]
    unique = {
        (candidate.group, candidate.intent, str(candidate.entities)): candidate
        for candidate in candidates
    }
    if len(unique) > 1:
        return RouteDecision('control', 'clarify', 'R06_COMPETING', clarification_required=True)
    candidate = next(iter(unique.values()))
    return _decision(candidate.group, candidate.intent, 'R05_EXPLICIT', **candidate.entities)


def _is_cancel_flow(text):
    return re.search(
        r'\b(cancel|stop|forget) (this|the|current) (check|flow|request)\b',
        text,
        re.I,
    )

def _is_negated_booking_cancel(item):
    return any(
        candidate.group == 'booking' and candidate.intent == 'cancel'
        for candidate in item.candidates
    ) and item.negation


def _initial_decision(item, text):
    if not text or item.request.message_type != 'text':
        return _decision('fallback', 'empty', 'R01_INPUT')
    if item.distress_signals:
        return _decision('support', item.distress_signals[0], 'R02_SUPPORT')
    if _is_cancel_flow(text):
        return _decision('control', 'cancel', 'R03_CANCEL_FLOW')
    if _is_negated_booking_cancel(item):
        return _decision('fallback', 'no_action', 'R03_NEGATED')
    return None


def _pending_decision(item, text, context):
    pending = context.get('pending_question')
    if not pending:
        return None
    if re.match(r"^(?:actually|correction|instead|i meant)\b", text, re.I):
        return _decision(context['active_group'], context['active_intent'], 'R03_CORRECTION')
    if _is_slot_answer(text, item, pending) and not any(
        candidate.specificity > 1 for candidate in item.candidates
    ):
        return _decision(context['active_group'], context['active_intent'], 'R04_VALID_SLOT')
    return None


def _remaining_decision(item, text, context):
    result = _explicit_candidate(item)
    if result:
        return result
    if re.fullmatch(r'(hi|hello|hey|hi archi|hello archi|thanks|thank you)[!. ]*', text, re.I):
        return _decision('fallback', 'greeting', 'R07_CONVERSATION')
    if context.get('pending_question'):
        return _decision(context['active_group'], context['active_intent'], 'R04_FOLLOWUP')
    if item.entity_spans:
        return _decision('course', 'overview', 'R05_COURSE')
    return _decision('fallback', 'unsupported', 'R08_UNKNOWN')


def route(i, context):
    t = i.original_text.strip()
    result = _initial_decision(i, t)
    if result:
        return result

    result = _clarification(t, context)
    if result:
        return result

    result = _pending_decision(i, t, context)
    if result:
        return result
    return _remaining_decision(i, t, context)
