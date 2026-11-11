"""Shared handler context and result construction."""
import re
from routing.models import HandlerResult
from routing.context import fresh_context

def _apply_correction(ctx, slots, courses, text):
    field = ctx.get('pending_question')
    correction = re.search(r'\b(passed|taken|term|course)\b', text, re.I)
    if correction:
        field = {'passed': 'passed_courses', 'taken': 'taken_courses'}.get(
            correction[1].lower(), correction[1].lower()
        )
    if field == 'course' and len(courses) == 1:
        slots.clear()
        slots['course'] = courses[0]
        ctx['pending_question'] = 'course'
    elif field in ('passed_courses', 'taken_courses'):
        ctx['pending_question'] = field
        slots.pop(field, None)
        slots.pop('term', None)


def prepare(d, i, context):
    continuing = context.get('active_group') == d.group and context.get('active_intent') == d.intent
    ctx = context if continuing or d.group == 'control' else fresh_context()
    slots = ctx['slots']
    courses = list(dict.fromkeys(m['code'] for m in i.entity_spans)) or d.entities.get('course_codes', [])
    if d.rule_id == 'R03_CORRECTION':
        _apply_correction(ctx, slots, courses, i.original_text)

    def result(text, status='answered', keep=False, action=None):
        return HandlerResult(status, {'text': text}, ctx if keep else fresh_context(), action)
    def ask(field, text):
        ctx.update(active_group=d.group, active_intent=d.intent, pending_question=field)
        return result(text, 'needs_input', True)
    return ctx, slots, courses, continuing, result, ask

