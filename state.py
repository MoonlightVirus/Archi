"""
Session-state initialization and sample/demo data for ARCHI.
Swap the sample data here for real API/database calls when wiring up a backend.
"""

import streamlit as st
import uuid
import re
from datetime import date, timedelta

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


def init_session_state():
    if "initialized" in st.session_state:
        return
    st.session_state.initialized = True
    st.session_state.logged_in = False
    st.session_state.auth_view = "login"          # "login" or "register"
    st.session_state.page = "dashboard"            # dashboard | chat | chats_list | book_consultation
    st.session_state.sidebar_open = True
    st.session_state.profile = DEFAULT_PROFILE.copy()
    st.session_state.chats = {}
    st.session_state.active_chat_id = None
    st.session_state.bookings = []
    st.session_state.pending_booking = None         # holds advisor/date/time while the modal is open
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
        or re.search(r"\b(consult\w*|appointment\w*|meeting\w*|session\w*)\b"
                     r".{0,40}\b(with|for)\b", msg)
    )


_TITLE_MAP = {
    "professor": "Prof.", "prof": "Prof.", "dr": "Dr.", "mr": "Mr.", "mrs": "Mrs.",
    "ms": "Ms.", "miss": "Miss", "sir": "Sir", "madam": "Madam", "ma'am": "Ma'am",
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
        r"\b(professor|prof|dr|mr|mrs|ms|miss|madam|sir|ma'?am)(?:\.)?\s+"
        r"[A-Za-z][A-Za-z'’-]*(?:\s+[A-Za-z][A-Za-z'’-]*)?",
        user_msg, re.IGNORECASE)
    if not m:
        return None
    parts = m.group(0).split()
    title = _TITLE_MAP.get(parts[0].rstrip(".").lower(), parts[0].capitalize())
    name = " ".join(w[:1].upper() + w[1:] for w in parts[1:])
    return f"{title} {name}"


def extract_booking_details(user_msg):
    """Pull booking specifics (topic, notes, date) mentioned by the user, if any."""
    details = {}
    msg_lower = user_msg.lower()

    for topic, keywords in _TOPIC_KEYWORDS.items():
        if any(k in msg_lower for k in keywords):
            details["topic"] = topic
            break

    if "tomorrow" in msg_lower:
        details["date"] = date.today() + timedelta(days=1)
    elif "next week" in msg_lower:
        details["date"] = date.today() + timedelta(days=7)
    else:
        m = re.search(r"\bon\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", msg_lower)
        if m:
            weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            delta = (weekdays.index(m.group(1)) - date.today().weekday() + 6) % 7 + 1
            details["date"] = date.today() + timedelta(days=delta)

    m = re.search(r"\b(?:about|regarding|concerning|to discuss)\s+(.+?)(?:[,.?!]|$)", user_msg, re.IGNORECASE)
    if m:
        phrase = m.group(1).strip()
        if phrase and not any(w in phrase.lower() for w in ("consult", "appointment", "meeting")):
            notes = phrase[:1].upper() + phrase[1:]
            details["notes"] = notes
            if "topic" not in details and len(notes) < 60:
                details["topic"] = notes

    return details


def get_advisors():
    """Session advisor list — seeded from ADVISORS, grows as new professors are mentioned."""
    if "advisors" not in st.session_state:
        st.session_state.advisors = ADVISORS.copy()
    return st.session_state.advisors


def register_advisor(name):
    """Add a professor mentioned in chat to the session advisor list."""
    if not name:
        return None
    advisors = get_advisors()
    if not any(a["name"].lower() == name.lower() for a in advisors):
        advisors.append({"name": name, "role": "Mentioned in Chat", "available": True})
    return name


def find_advisor(user_msg):
    """Return the professor mentioned in the message, registering new ones dynamically."""
    msg = user_msg.lower()
    for advisor in get_advisors():
        if advisor["name"].lower() in msg:
            return advisor["name"]
    return register_advisor(extract_professor(user_msg))
