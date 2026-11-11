from dataclasses import asdict
from copy import deepcopy
from .models import ConversationContext

def fresh_context():
    return asdict(ConversationContext())

def normalize_context(context=None):
    result = fresh_context()
    result.update(deepcopy(context or {}))
    return result

def migrate_chat(chat):
    chat['context'] = normalize_context(chat.get('context'))
    chat.setdefault('pending_message_id', None)
    chat.setdefault('last_processed_message_id', None)
    chat.setdefault('processed_results', {})
    return chat
