"""
Session-state initialization and sample/demo data for ARCHI.
Swap the sample data here for real API/database calls when wiring up a backend.
"""

import streamlit as st
import uuid
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
