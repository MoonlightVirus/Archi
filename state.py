"""
Session-state initialization and sample/demo data for ARCHI.
Swap the sample data here for real API/database calls when wiring up a backend.
"""

import streamlit as st
import uuid
import re
import calendar
from difflib import SequenceMatcher
from datetime import date, timedelta, datetime

from chatbot_engine import get_response as archi_get_response


DEFAULT_PROFILE = {
    "name": "Juan Dela Cruz",
    "role": "Student",
    "program": "BSCS",
    "course": "CBPROG1",
    "gpa": 2.0,
    "status": "DELAYED",
    "advisor": "Mr. Morales",
}

ADVISORS = [
    {"name": "Dr. Reyes", "role": "CBL Coordinator", "available": True},
    {"name": "Mr. Morales", "role": "BSCS Coordinator", "available": True},
    {"name": "Ms. Santos", "role": "Academic Advisor", "available": False},
]

CURRICULUM = [
    {"term": "1st Year, Term 1", "courses": [
        {"code": "CBPROG1", "title": "Introduction to Computing", "status": "in_progress"},
        {"code": "GENMATH", "title": "General Mathematics", "status": "completed"},
        {"code": "PURCOMM", "title": "Purposive Communication", "status": "completed"},
    ]},
    {"term": "1st Year, Term 2", "courses": [
        {"code": "CBPROG2", "title": "Intermediate Programming", "status": "locked"},
        {"code": "DISCMATH", "title": "Discrete Mathematics", "status": "locked"},
        {"code": "ARTAPPR", "title": "Art Appreciation", "status": "locked"},
    ]},
]

TOPIC_OPTIONS = [
    "Course Prerequisite Override",
    "GPA Recovery Plan",
    "Flowchart Review",
    "Enrollment Concern",
    "Other",
]

MODALITIES = ["Online", "F2F"]
PLACES_BY_MODALITY = {
    "Online": ["Google Meet", "Zoom Video Call"],
    "F2F": ["Yuchengco Hall — Room 207", "Henry Sy Hall — Room 402", "AVR — Ground Floor"],
}


def _seed_chats():
    """First chat matches the mockup conversation; the rest are placeholder history."""
    first_chat_id = str(uuid.uuid4())
    chats = {
        first_chat_id: {
            "title": "Archi's First Chat!",
            "messages": [
                ("user", "text", "Hi Archi!"),
                ("assistant", "text", "Hi I'm Archi! Your personal academic assistant!"),
                ("user", "text", "I need help with my flowchart"),
                ("assistant", "text", "Okay! I understand your situation, allow me to help! Please upload your flowchart first and I will analyze and provide suggestions!"),
                ("user", "file", "flowchart.pdf"),
            ],
        }
    }
    ordinals = ["Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh",
                "Eight", "Ninth", "Tenth", "Eleventh"]
    for ordinal in ordinals:
        chats[str(uuid.uuid4())] = {
            "title": f"Archi's {ordinal} Chat!",
            "messages": [
                ("user", "text", "Hi Archi!"),
                ("assistant", "text", "Hi I'm Archi! Your personal academic assistant! How can I help you today?"),
            ],
        }
    return chats, first_chat_id


def init_session_state():
    if "initialized" in st.session_state:
        return
    chats, first_chat_id = _seed_chats()
    st.session_state.initialized = True
    st.session_state.logged_in = False
    st.session_state.auth_view = "login"          # "login" or "register"
    st.session_state.page = "dashboard"            # dashboard | chat | chats_list | book_consultation
    st.session_state.sidebar_open = True
    st.session_state.profile = DEFAULT_PROFILE.copy()
    st.session_state.chats = chats
    st.session_state.active_chat_id = first_chat_id
    st.session_state.bookings = []
    st.session_state.pending_booking = None         # holds advisor/date/time while the modal is open
    st.session_state.draft_email = None             # holds the built consultation email draft
    st.session_state.show_settings = False


def go(page):
    st.session_state.page = page
    st.rerun()


def new_chat():
    chat_id = str(uuid.uuid4())
    n = len(st.session_state.chats) + 1
    st.session_state.chats[chat_id] = {"title": f"New Chat {n}", "messages": []}
    st.session_state.active_chat_id = chat_id
    st.session_state.page = "chat"
    st.rerun()


def bot_reply(user_msg):
    """Placeholder rule-based reply — swap for a real backend/LLM call."""
    msg = user_msg.lower()
    p = st.session_state.profile
    """
    if "flowchart" in msg or "curriculum" in msg:
        return "Please upload your flowchart first and I will analyze and provide suggestions!"
    if "gpa" in msg:
        return f"Your current GPA is {p['gpa']:.1f} ({p['status']}). Want me to help you plan a recovery strategy?"
    if "consult" in msg or "advisor" in msg:
        return f"Your current advisor is {p['advisor']}. I can help you book a consultation — just head to Book a Consultation."
    """
    
    return archi_get_response(user_msg)


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
    today = date.today()
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
    today = date.today()
    tl = text.lower()

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


def get_advisors():
    """Session advisor list — seeded from ADVISORS, grows as new professors are mentioned."""
    if "advisors" not in st.session_state:
        st.session_state.advisors = ADVISORS.copy()
    return st.session_state.advisors


def _same_person(name_a, name_b):
    """Fuzzy name match — same surname (or close to it) means the same person."""
    a, b = name_a.lower(), name_b.lower()
    if a == b:
        return True
    sa, sb = a.split()[-1], b.split()[-1]
    return sa in sb or sb in sa or SequenceMatcher(None, sa, sb).ratio() >= 0.8


def _normalize_date(value):
    """Return an ISO 'YYYY-MM-DD' string for a date object or formatted date string."""
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, str):
        for fmt in ("%B %d, %Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
    return None


def get_day_bookings(day):
    """Consultations on a given date: 'Email Sent', 'Pending', or 'Cancelled'."""
    iso = _normalize_date(day)
    if not iso:
        return []
    result = []
    for b in st.session_state.get("bookings", []):
        if _normalize_date(b.get("date")) == iso:
            result.append({
                "advisor": b.get("advisor", ""),
                "time": b.get("time", ""),
                "place": b.get("place", ""),
                "modality": b.get("modality", ""),
                "status": "Email Sent" if b.get("status") == "sent" else "Cancelled",
            })
    draft = st.session_state.get("draft_email")
    if draft and not st.session_state.get("email_sent"):
        draft_date = draft.get("date") or st.session_state.get("selected_date")
        if _normalize_date(draft_date) == iso:
            result.append({
                "advisor": draft.get("advisor", ""),
                "time": draft.get("time") or st.session_state.get("selected_time", "9:00 AM"),
                "place": draft.get("place") or st.session_state.get("selected_place", "Google Meet"),
                "modality": draft.get("modality") or st.session_state.get("selected_modality", "Online"),
                "status": "Pending",
            })
    return result


def register_advisor(name, email=None, role="Mentioned in Chat"):
    """Add a professor to the session advisor list (deduped by name)."""
    if not name:
        return None
    advisors = get_advisors()
    for a in advisors:
        if _same_person(a["name"], name):
            if email:
                a["email"] = email
            return a["name"]
    advisors.append({"name": name, "role": role, "available": True, "email": email})
    return name


def find_advisor_entry(name):
    """Return the advisor dict for a name (fuzzy match), if known."""
    for a in get_advisors():
        if _same_person(a["name"], name):
            return a
    return None


def update_advisor(original_name, name=None, role=None, email=None, available=None):
    """Edit an advisor's details in the session list (keeps selection in sync)."""
    for a in get_advisors():
        if _same_person(a["name"], original_name):
            if name is not None and name.strip():
                a["name"] = name.strip()
            if role is not None:
                a["role"] = role.strip() or a.get("role", "")
            if email is not None:
                a["email"] = email.strip() or None
            if available is not None:
                a["available"] = bool(available)
            if _same_person(st.session_state.get("selected_advisor", ""), original_name):
                st.session_state.selected_advisor = a["name"]
            return a
    return None


def find_advisor(user_msg):
    """Return the professor mentioned in the message, registering new ones dynamically."""
    msg = user_msg.lower()
    for advisor in get_advisors():
        if advisor["name"].lower() in msg:
            return advisor["name"]
    name = extract_professor(user_msg)
    if not name:
        return None
    for advisor in get_advisors():
        if _same_person(advisor["name"], name):
            return advisor["name"]
    return register_advisor(name)


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


def cancel_consultation(user_msg):
    """Cancel the pending consultation/draft for the professor mentioned, if any."""
    draft = st.session_state.get("draft_email") or {}
    pending = draft.get("advisor") or st.session_state.get("selected_advisor")
    mentioned = find_advisor(user_msg)

    if mentioned and pending and not _same_person(mentioned, pending):
        return None

    target = pending or mentioned or st.session_state.profile.get("advisor")

    st.session_state.draft_email = None
    for key in ("email_mode", "email_to", "email_subject", "email_body"):
        st.session_state.pop(key, None)
    st.session_state.email_sent = False
    st.session_state.pop("selected_advisor", None)
    st.session_state.pop("book_consultation_tabs", None)
    st.session_state.pending_booking = None

    for b in st.session_state.get("bookings", []):
        if (b.get("status") == "sent" and target
                and _same_person(b.get("advisor", ""), target)):
            b["status"] = "cancelled"

    # remove the cancelled professor from the session advisor list
    if target:
        advisors = get_advisors()
        advisors[:] = [a for a in advisors if not _same_person(a["name"], target)]
        if not advisors:
            advisors.extend(ADVISORS.copy())

    return target
