from zoneinfo import ZoneInfo
from .parser import parse_booking_request, extract_professor
from routing.handlers.common import prepare

def handle(d, i, context, services=None):
    ctx, slots, courses, continuing, result, ask = prepare(d, i, context)
    if services is None:
        return result('Consultation services are unavailable.', 'unsupported')
    if d.intent == 'cancel':
        records = services.list_records(i.request.chat_id)
        matched = [r for r in records if r.get('id', '') in i.original_text]
        if not matched and len(records) == 1:
            matched = records
        if len(matched) != 1:
            return ask('booking_id', 'Which draft or booking should I cancel? Provide its ID: ' + ', '.join(r.get('id', '') for r in records))
        services.cancel(matched[0]['id'], i.request.chat_id)
        return result('Cancelled the selected consultation draft or booking.', 'cancelled')
    local = i.request.timestamp.astimezone(ZoneInfo(i.request.timezone))
    fields, errors, notes = parse_booking_request(i.original_text, local.date(), i.request.timezone)
    name = extract_professor(i.original_text)
    if name:
        fields['advisor'] = name
    if fields.get('modality') and fields.get('modality') != slots.get('modality'):
        slots.pop('place', None)
    slots.update(fields)
    if slots.get('date') and slots['date'] < local.date():
        errors.append('Please choose today or a future date.')
    if errors:
        return ask('booking_details', 'Please correct: ' + '; '.join(errors))
    required = ['advisor', 'date', 'time', 'modality', 'place']
    missing = [f for f in required if not slots.get(f)]
    if missing:
        return ask('booking_details', 'To prepare a consultation draft, please provide: ' + ', '.join(missing) + '.')
    draft = services.prepare_draft(slots, i.request.chat_id, i.request.message_id)
    return result('Prepared a consultation email draft for review. No email has been sent.', 'draft_created', action={'navigation': 'book_consultation', 'draft_id': draft['id']})
