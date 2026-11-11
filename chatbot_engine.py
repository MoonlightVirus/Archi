"""Single turn orchestrator. Interpretation and routing have no application effects."""
import logging
from uuid import uuid4
from routing.models import MessageRequest, TurnResult, HandlerResult
from routing.context import normalize_context, migrate_chat
from routing.interpreter import interpret
from routing.router import route
from routing.handlers import handle
from dialogue.turn_renderer import render
logger = logging.getLogger(__name__)

def process_message(request, context=None, services=None):
    context = normalize_context(context)
    interpretation = interpret(request, context)
    decision = route(interpretation, context)
    try:
        outcome = handle(decision, interpretation, context, services)
    except Exception:
        logger.error('Handler failed group=%s intent=%s', decision.group, decision.intent)
        outcome = HandlerResult('error', {'text': 'I could not complete that request. Please try again.'}, context)
    metadata = dict(group=decision.group, intent=decision.intent, rule_id=decision.rule_id,
                    status=outcome.status, transition=f"{context.get('pending_question')}->{outcome.context.get('pending_question')}")
    logger.info('route=%s', metadata)
    return TurnResult(render(outcome), outcome.context,
                      (outcome.action_request or {}).get('navigation'), metadata)

def process_chat_message(chat, request, services=None):
    migrate_chat(chat)
    if request.message_id in chat['processed_results']:
        return chat['processed_results'][request.message_id]
    result = process_message(request, chat['context'], services)
    chat['context'] = result.context
    chat['messages'].append(dict(role='assistant', content=result.reply, reply_to=request.message_id))
    chat['processed_results'][request.message_id] = result
    chat['last_processed_message_id'] = request.message_id
    chat['pending_message_id'] = None
    return result

def get_response(user_input):
    """Compatibility entry point for stateless callers."""
    return process_message(MessageRequest('stateless', str(uuid4()), user_input)).reply
