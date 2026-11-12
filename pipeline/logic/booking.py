"""Consultation parsing and multi-turn booking, independent of the UI."""
import re
import calendar
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo
from pipeline.context import PipelineContext, clear_workflow

MODALITIES = ["Online", "F2F"]
PLACES_BY_MODALITY = {
    "Online": ["Google Meet", "Zoom Video Call"],
    "F2F": ["Yuchengco Hall — Room 207", "Henry Sy Hall — Room 402", "AVR — Ground Floor"],
}


def detect_booking_intent(user_msg):
    """True when the user is asking to book/schedule a consultation."""
    msg = user_msg.lower()
    return bool(
        re.search(r"\b(book|schedule|set\s*up|reserve|request|arrange|make)\b"
                  r".{0,40}\b(consult\w*|appointment\w*|meeting\w*|session\w*|advisor\w*|professor\w*)\b", msg)
        or re.search(r"\b(book|schedule|set\s*up|reserve|request|arrange|make)\b"
                     r".{0,40}\b(professor|prof|doc|dr|mr|mrs|ms|miss|madam|mam|maam|sir)\b", msg)
        or re.search(r"\b(consult\w*|appointment\w*|meeting\w*|session\w*)\b"
                     r".{0,40}\b(with|for)\b", msg)
    )


_TITLE_MAP = {
    "professor": "Prof.", "prof": "Prof.", "doc": "Dr.", "dr": "Dr.", "mr": "Mr.", "mrs": "Mrs.",
    "ms": "Ms.", "miss": "Miss", "sir": "Sir", "madam": "Madam", "mam": "Ma'am",
    "maam": "Ma'am", "ma'am": "Ma'am",
}

_STOP_WORDS = {"off", "the", "of", "with", "for", "about", "my", "to", "and", "in",
               "on", "a", "an", "is", "at", "please", "this", "that", "from",
               "consult", "consultation", "appointment", "meeting", "booking",
               "schedule", "advisor", "professor"}

_NAME_BREAK_WORDS = _STOP_WORDS | {
    "online", "f2f", "virtual", "face", "am", "pm", "today", "tomorrow",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "morning", "afternoon", "evening", "now", "soon", "later", "next",
}

_TOPIC_KEYWORDS = {
    "Course Prerequisite Override": ["prereq", "prerequisite", "override", "load"],
    "GPA Recovery Plan": ["gpa", "recovery", "grade", "academic probation"],
    "Flowchart Review": ["flowchart", "flow chart", "curriculum"],
    "Enrollment Concern": ["enroll", "enrollment", "registration", "block", "section"],
}


def extract_professor(user_msg):
    """Extract a professor name (e.g. 'Ms. Romualde') mentioned in the message."""
    m = re.search(
        r"\b(professor|prof|doc|dr|mr|mrs|ms|miss|madam|mam|maam|sir|ma'?am)(?:\.)?\s+"
        r"[A-Za-z][A-Za-z'’-]*(?:\s+[A-Za-z][A-Za-z'’-]*)?",
        user_msg, re.IGNORECASE)
    if not m:
        return None
    parts = m.group(0).split()
    title = _TITLE_MAP.get(parts[0].rstrip(".").lower(), parts[0].capitalize())
    names = []
    for word in parts[1:]:
        if len(word) <= 1 or word.lower() in _NAME_BREAK_WORDS:
            break
        names.append(word)
    if not names:
        return None
    name = " ".join(w[:1].upper() + w[1:] for w in names)
    return f"{title} {name}"


TIME_SLOTS = [f"{h if h <= 12 else h - 12}:{m:02d} {'AM' if h < 12 else 'PM'}"
              for h in range(8, 19) for m in (0, 30)]

_MONTH_ABBREV = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
                 "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}


def _validate_date(year, month, day):
    """Return (date, error) after range-checking year/month/day."""
    today = datetime.now(ZoneInfo("Asia/Manila")).date()
    problems = []
    if not (today.year - 1 <= year <= today.year + 5):
        problems.append(f"year {year} is out of range — please pick between {today.year - 1} and {today.year + 5}")
    if not (1 <= month <= 12):
        problems.append(f"month {month} is invalid — months are 1–12")
    max_day = calendar.monthrange(year, month)[1] if 1 <= month <= 12 else 31
    if not (1 <= day <= max_day):
        problems.append(f"day {day} is invalid — {calendar.month_name[month] if 1 <= month <= 12 else month} "
                        f"{year} only has {max_day} days")
    if problems:
        return None, "; ".join(problems) + "."
    return date(year, month, day), None


def _parse_date(text):
    """Return (date, error) parsed from natural-language date mentions."""
    today = datetime.now(ZoneInfo("Asia/Manila")).date()
    tl = text.lower()

    iso = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", tl)
    if iso:
        return _validate_date(*(int(part) for part in iso.groups()))
    if re.search(r"\btoday\b", tl):
        return today, None
    if "tomorrow" in tl:
        return today + timedelta(days=1), None
    if "next week" in tl:
        return today + timedelta(days=7), None

    m = re.search(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", tl)
    if m:
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        delta = (weekdays.index(m.group(1)) - today.weekday() + 6) % 7 + 1
        return today + timedelta(days=delta), None

    month_names = "|".join(list(_MONTH_ABBREV) + ["december", "november", "october",
                                                  "september", "august", "july", "june",
                                                  "may", "april", "march", "february", "january"])
    m = re.search(rf"\b({month_names})\.?\s+(\d{{1,2}})(?:,?\s+(\d{{2,4}}))?", text, re.IGNORECASE)
    if m:
        month = _MONTH_ABBREV.get(m.group(1)[:3].lower())
        day = int(m.group(2))
        year = int(m.group(3)) if m.group(3) else today.year
        if year < 100:
            year += 2000
        return _validate_date(year, month, day)

    m = re.search(r"\b(\d{1,2})[-/](\d{1,2})(?:[-/](\d{2,4}))?\b", text)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        year = int(m.group(3)) if m.group(3) else today.year
        if year < 100:
            year += 2000
        if 1 <= a <= 12 and 1 <= b <= 31:
            res = _validate_date(year, a, b)
            if not res[1]:
                return res
        return _validate_date(year, b, a)

    return None, None


def _parse_time(text):
    """Return (time_str like '5:00 PM', error) parsed from natural-language times."""
    tl = text.lower()
    m = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)\b", tl)
    if m:
        hour, minute = int(m.group(1)), int(m.group(2)) if m.group(2) else 0
        ampm = m.group(3).replace(".", "")
        if not (1 <= hour <= 12):
            return None, f"'{hour}:{minute:02d} {ampm.upper()}.' has an invalid hour — use 1–12."
        if not (0 <= minute <= 59):
            return None, (f"'{hour}:{m.group(2)} {ampm.upper()}.' has invalid minutes "
                          f"— use 0–59 (e.g. 5:30 PM).")
        h24 = (hour % 12) + (0 if ampm.startswith("a") else 12)
    else:
        m = re.search(r"\b(\d{1,2}):(\d{2})\b", tl)
        if not m:
            return None, None
        hour, minute = int(m.group(1)), int(m.group(2))
        if not (0 <= hour <= 23):
            return None, f"'{hour}:{minute:02d}' has an invalid hour — use 0–23."
        if not (0 <= minute <= 59):
            return None, f"'{hour}:{minute:02d}' has invalid minutes — use 0–59."
        h24 = hour

    h12 = h24 % 12
    if h12 == 0:
        h12 = 12
    time_str = f"{h12}:{minute:02d} {'AM' if h24 < 12 else 'PM'}"
    if time_str not in TIME_SLOTS:
        return None, (f"'{time_str}' is outside the available booking window "
                      f"({TIME_SLOTS[0]} – {TIME_SLOTS[-1]}, every 30 minutes).")
    return time_str, None


def _parse_modality(text):
    tl = text.lower()
    if re.search(r"\b(online|virtual|google meet|zoom)\b", tl):
        return "Online"
    if re.search(r"\b(f2f|face[- ]to[- ]face|onsite|in person|in-person|physical)\b", tl):
        return "F2F"
    return None


def _parse_place(text):
    tl = text.lower()
    if "yuchengco" in tl or "yuchenco" in tl:
        return "Yuchengco Hall — Room 207"
    if "henry sy" in tl:
        return "Henry Sy Hall — Room 402"
    if re.search(r"\bavr\b", tl):
        return "AVR — Ground Floor"
    if "google meet" in tl:
        return "Google Meet"
    if "zoom" in tl:
        return "Zoom Video Call"
    return None


def parse_booking_request(user_msg):
    """Dissect a booking message into (details, errors, notes).

    - details: validated date/time/modality/place/topic/notes
    - errors:  blocking issues (out-of-range date/time/place conflicts) for the bot to report
    - notes:   soft adjustments the bot should mention but not block on
    """
    errors, notes = [], []
    details = {}
    msg_lower = user_msg.lower()

    for topic, keywords in _TOPIC_KEYWORDS.items():
        if any(k in msg_lower for k in keywords):
            details["topic"] = topic
            break
    m = re.search(r"\b(?:about|regarding|concerning|to discuss)\s+(.+?)(?:[,.?!]|$)", user_msg, re.IGNORECASE)
    if m:
        phrase = m.group(1).strip()
        if phrase and not any(w in phrase.lower() for w in ("consult", "appointment", "meeting")):
            notes_text = phrase[:1].upper() + phrase[1:]
            details["notes"] = notes_text
            if "topic" not in details and len(notes_text) < 60:
                details["topic"] = notes_text

    day, derr = _parse_date(user_msg)
    if derr:
        errors.append(f"Date: {derr}")
    elif day:
        details["date"] = day

    time_str, terr = _parse_time(user_msg)
    if terr:
        errors.append(f"Time: {terr}")
    elif time_str:
        details["time"] = time_str

    place = _parse_place(user_msg)
    modality = _parse_modality(user_msg)
    place_modality = next((mod for mod, places in PLACES_BY_MODALITY.items() if place in places), None)
    if place:
        details["place"] = place
    if modality:
        details["modality"] = modality
    if place_modality and modality and place_modality != modality:
        details["modality"] = place_modality
        notes.append(f"Note: {place} is a {place_modality} venue, so I set the meeting to {place_modality}.")
    elif place_modality:
        details["modality"] = place_modality

    return details, errors, notes


def extract_booking_details(user_msg):
    """Backward-compatible wrapper: only the parsed details (no errors)."""
    details, _errors, _notes = parse_booking_request(user_msg)
    return details


def detect_cancel_intent(user_msg):
    """True when the user wants to cancel or delete a consultation booking."""
    msg = user_msg.lower()
    cancel_words = ["cancel", "cancelled", "canceled", "delete", "remove", "drop",
                    "unbook", "take off", "get rid of", "scrap"]
    if not any(w in msg for w in cancel_words):
        return False
    context_words = ["consult", "appointment", "booking", "meeting", "schedule",
                     "advisor", "professor", "email", "draft"]
    if any(w in msg for w in context_words):
        return True
    return extract_professor(user_msg) is not None




_REQUIRED = ("advisor", "date", "time", "modality", "place")
_FIELDS = (*_REQUIRED, "topic", "notes")


def process_booking(ctx: PipelineContext, booking_service=None) -> str:
    """Collect validated slots and emit a draft for the UI to review."""
    session = ctx.session_state
    if ctx.intent == "cancel_consultation":
        advisor = ctx.entities.get("advisor") or session["slots"].get("advisor")
        clear_workflow(session)
        session["completed_booking"] = None
        session.pop("booking_errors", None)
        session["cancelled_booking"] = {"advisor": advisor}
        ctx.status = "cancelled"
        return "I've cleared the consultation draft."
    if session.get("active_workflow") != "Booking":
        clear_workflow(session)
        session["completed_booking"] = None
        session.pop("booking_errors", None)
    slots = session["slots"]
    errors = dict(session.get("booking_errors") or {})
    for field in _FIELDS:
        value = ctx.entities.get(field)
        if value is not None:
            slots[field] = value
            errors.pop(field, None)
    for message in ctx.entities.get("booking_errors", []):
        field = message.split(":", 1)[0].lower()
        errors[field] = message
        slots.pop(field, None)
    if slots.get("date") and slots["date"] < datetime.now(ZoneInfo("Asia/Manila")).date():
        errors["date"] = "Date: please choose today or a future date."
        slots.pop("date", None)
    if slots.get("time") and slots["time"] not in TIME_SLOTS:
        errors["time"] = "Time: please choose an available half-hour slot between 8:00 AM and 6:30 PM."
        slots.pop("time", None)
    if slots.get("modality") and slots["modality"] not in MODALITIES:
        errors["modality"] = "Modality: please choose Online or F2F."
        slots.pop("modality", None)
    if slots.get("place") and slots.get("modality") and slots["place"] not in PLACES_BY_MODALITY[slots["modality"]]:
        errors["place"] = "Place: please choose a venue matching the meeting modality."
        slots.pop("place", None)
    session["booking_errors"] = errors
    missing = [field for field in _REQUIRED if not slots.get(field)]
    if errors or missing:
        ctx.status = "needs_input"
        session.update(active_workflow="Booking", pending_slot=missing[0] if missing else next(iter(errors)))
        problems = "\n".join(errors.values())
        prompt = "Please provide the consultation " + ", ".join(missing) + "." if missing else "Please correct these consultation details."
        return (problems + "\n\n" if problems else "") + prompt
    draft = dict(slots)
    # The optional service is an injected callable accepting the finalized draft.
    # Leave the workflow intact if it raises, so the caller can retry.
    if booking_service is not None:
        booking_service(dict(draft))
    clear_workflow(session)
    session.pop("booking_errors", None)
    session["completed_booking"] = draft
    ctx.status = "draft_created"
    note = "\n\n" + "\n".join(ctx.entities.get("booking_notes", [])) if ctx.entities.get("booking_notes") else ""
    return (f"I've prepared a consultation draft with {draft['advisor']} on "
            f"{draft['date']:%B %d, %Y} at {draft['time']} "
            f"({draft['modality']} · {draft['place']}). Review and edit the email before sending." + note)


handle_booking = process_booking
