"""
Session-state initialization and sample/demo data for ARCHI.
Swap the sample data here for real API/database calls when wiring up a backend.
"""

import streamlit as st
import uuid
from difflib import SequenceMatcher
from datetime import datetime

from chatbot_engine import get_response as archi_get_response
from pipeline.logic.booking import (
    MODALITIES, PLACES_BY_MODALITY, TIME_SLOTS, detect_booking_intent,
    detect_cancel_intent, extract_professor, parse_booking_request, extract_booking_details,
)


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


def bot_reply(user_msg, session_state=None, *, message_id=None):
    """Delegate one turn using the current chat's conversation state."""
    return archi_get_response(user_msg, session_state, message_id=message_id)


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
