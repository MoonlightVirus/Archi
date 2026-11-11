from routing.preprocessor import preprocess_text
from logic.course.intent_classifier import INTENT_PATTERNS
from .models import Interpretation, IntentCandidate
from .courses import resolve_courses, suggest_courses
from .support import distress
from logic.booking.parser import detect_booking_intent
import json
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ENTITIES = json.loads((ROOT/'logic/academic/academic_entities.json').read_text())
RULES = json.loads((ROOT/'logic/academic/intent_to_rule_map.json').read_text())

def _candidate(group, intent, evidence, specificity=3, **entities):
    return IntentCandidate(group, intent, entities, [evidence], specificity)


def _booking_candidates(text, booking):
    candidates = []
    policy = re.search(r'\b(policy|rules?|how does|what is)\b', text, re.I)
    if booking and re.search(r'\b(cancel|delete|remove)\b', text, re.I) and not policy:
        candidates.append(_candidate('booking', 'cancel', 'cancel consultation'))
    elif detect_booking_intent(text):
        candidates.append(_candidate('booking', 'draft', 'schedule consultation'))
    if booking and policy:
        candidates.append(_candidate('academic', 'consultation_policy', 'consultation policy'))
    return candidates


def _academic_candidates(text, booking):
    # A booking topic is a separate academic request only with an explicit conjunction.
    separate_request = not booking or bool(re.search(r'\b(and|also)\b', text, re.I))
    rules = (
        ('prerequisites', r'\bprerequisites?\b', 'prerequisite', separate_request),
        ('eligibility', r'\b(eligible|eligibility|can i take|can i enroll|allowed to take)\b', 'eligibility', True),
        ('gpa', r'\bgpa|cgpa\b', 'GPA', separate_request),
        ('flowchart', r'\bflow\s*chart\b', 'flowchart', not booking),
        ('offerings', r'\boffered\b', 'offered term', True),
    )
    return [
        _candidate('academic', intent, evidence)
        for intent, pattern, evidence, allowed in rules
        if allowed and re.search(pattern, text, re.I)
    ]


def _course_candidates(text, candidates):
    has_academic = any(candidate.group == 'academic' for candidate in candidates)
    course_candidates = []
    for intent, pattern in INTENT_PATTERNS:
        m = pattern.search(text)
        if m and not (intent == 'tips' and has_academic):
            course_candidates.append(_candidate('course', intent, m.group()))
    return course_candidates


def _handbook_candidates(text):
    candidates = []
    for category, rule in RULES.items():
        for phrase in ENTITIES.get(category, []):
            if re.search(r'\b'+re.escape(phrase)+r'\b', text, re.I):
                candidates.append(_candidate('academic', 'handbook', phrase, len(phrase.split()), rule_id=rule))
    return candidates


def interpret(request, context):
    text = request.text
    p = preprocess_text(text)
    mentions = resolve_courses(text)
    booking = bool(re.search(r'\b(consultation|appointment|meeting|booking|draft)\b', text, re.I))
    negation = bool(re.search(r"\b(no|not|never|none|didn't|don't)\b", text, re.I))
    candidates = _booking_candidates(text, booking)
    candidates.extend(_academic_candidates(text, booking))
    candidates.extend(_course_candidates(text, candidates))
    if not candidates:
        candidates.extend(_handbook_candidates(text))
    if not mentions:
        suggestions = suggest_courses(text)
        if suggestions:
            candidates.append(_candidate('control', 'course_match', 'ambiguous course', 10, suggestions=suggestions))
    course_codes = list(dict.fromkeys(m['code'] for m in mentions))
    for candidate in candidates:
        candidate.entities['course_codes'] = course_codes.copy()
    return Interpretation(text, p['cleaned_tokens'], mentions, negation, candidates, distress(text), request)
