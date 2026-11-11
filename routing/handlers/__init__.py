"""Dispatch to the four isolated logic groups; shared control stays here."""
from routing.support import support_reply
from routing.handlers.common import prepare
from importlib import import_module

GROUPS = ('course', 'academic', 'booking', 'fallback')

def handle(d, i, context, services):
    if d.group in GROUPS:
        handler = import_module(f'logic.{d.group}.handler')
        return handler.handle(d, i, context, services)
    ctx, slots, courses, continuing, result, ask = prepare(d, i, context)
    if d.group == 'support':
        return result(support_reply(d.intent))
    if d.group == 'control':
        if d.intent == 'cancel':
            return result('Cancelled this conversation flow.', 'cancelled')
        if d.intent == 'course_match':
            ctx = context
            original = next((c for c in i.candidates if c.group in ('course', 'academic')), None)
            if original:
                ctx.update(active_group=original.group, active_intent=original.intent, pending_question='course')
            else:
                ctx.update(active_group='course', active_intent='overview', pending_question='course')
            return result('Please confirm the course code: ' + ', '.join(d.entities['suggestions']), 'needs_clarification', True)
        ctx = context
        ctx['clarification_options'] = [dict(group=c.group, intent=c.intent, entities=c.entities) for c in i.candidates]
        return result('Which request should I handle first? ' + ', '.join(c.intent for c in i.candidates), 'needs_clarification', True)
