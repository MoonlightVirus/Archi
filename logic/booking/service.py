"""Application effects isolated from parsing and routing."""
from uuid import uuid4

class BookingService:
    def __init__(self, state):
        self.state = state

    def list_records(self, chat_id):
        records = list(self.state.get('bookings', []))
        records += list(self.state.get('consultation_drafts', {}).values())
        draft = self.state.get('draft_email')
        if draft and not self.state.get('email_sent'):
            records.append(draft)
        return list({r.get('id'): r.copy() for r in records if r.get('chat_id') == chat_id and r.get('status') not in ('cancelled', 'sent')}.values()) + [r.copy() for r in self.state.get('bookings', []) if r.get('chat_id') == chat_id and r.get('status') == 'sent']

    def prepare_draft(self, fields, chat_id, message_id):
        existing = self.state.get('draft_email')
        if existing and existing.get('message_id') == message_id:
            return existing.copy()
        draft = dict(fields, id=str(uuid4()), chat_id=chat_id, message_id=message_id)
        self.state.setdefault('consultation_drafts', {})[draft['id']] = draft
        self.state['draft_email'] = draft
        for key in ('date', 'time', 'modality', 'place', 'advisor'):
            self.state['selected_' + key] = draft[key]
        self.state['cal_year'] = draft['date'].year
        self.state['cal_month'] = draft['date'].month
        self.state['email_sent'] = False
        return draft.copy()

    def cancel(self, record_id, chat_id):
        records = self.list_records(chat_id)
        if not any(r.get('id') == record_id for r in records):
            raise ValueError('That draft or booking is no longer available in this chat.')
        self.state.get('consultation_drafts', {}).pop(record_id, None)
        draft = self.state.get('draft_email') or {}
        if draft.get('id') == record_id:
            self.state['draft_email'] = None
            for key in ('email_mode', 'email_to', 'email_subject', 'email_body'):
                self.state.pop(key, None)
        for record in self.state.get('bookings', []):
            if record.get('id') == record_id and record.get('chat_id') == chat_id:
                record['status'] = 'cancelled'
