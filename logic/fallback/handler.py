import json
from pathlib import Path
from routing.models import HandlerResult
from routing.handlers.common import prepare

def handle(d, i, context, services=None):
    ctx, slots, courses, continuing, result, ask = prepare(d, i, context)
    if d.intent == 'greeting':
        try:
            from nltk.chat.util import Chat, reflections
            pairs = json.loads(Path(__file__).with_name('fallback_regex_pairs.json').read_text())
            reply = Chat(pairs, reflections).respond(i.original_text)
        except (ImportError, LookupError):
            reply = None
        return HandlerResult('answered', {'text': reply or 'Hello! I can help with courses, prerequisites, eligibility, handbook policies, or consultation drafts.'}, context)
    if d.intent == 'no_action':
        return HandlerResult('answered', {'text': 'Your consultation has been left unchanged.'}, context)
    return HandlerResult('unsupported', {'text': 'Please send a text question about a course, academic policy, eligibility, or a consultation. I cannot analyze attachments yet.'}, context)
