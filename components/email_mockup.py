"""
Email Mockup Component
----------------------
Gmail-style draft email for consultation requests. Two modes:

* preview — read-only rendering of the composed email with Edit / Send buttons.
* edit    — editable To / Subject / Message fields.

Everything is mockup: "sending" only appends to st.session_state.bookings.
"""

import html
from datetime import date

import streamlit as st

from state import find_advisor_entry

DEFAULT_TOPIC = "General Consultation"


def _fmt(value, fmt="%B %d, %Y"):
    if hasattr(value, "strftime"):
        return value.strftime(fmt)
    return str(value)


def _advisor_email(name):
    slug = name.lower().replace(".", "").replace(" ", ".")
    return f"{slug}@dlsu.edu.ph"


def _student_email():
    p = st.session_state.profile
    return f"{p['name'].lower().replace(' ', '.')}@dlsu.edu.ph"


def _compose_body(draft):
    """Default email body template for the draft."""
    p = st.session_state.profile
    lines = [
        f"Dear {draft['advisor']},",
        "",
        f"I hope this message finds you well. I am {p['name']}, a {p.get('program', '')} student. "
        f"I would like to request a consultation to discuss: {draft['topic']}.",
        "",
        f"I am available on {draft['date']} at {draft['time']} "
        f"({draft['modality']} · {draft['place']}). I am happy to adjust "
        f"to a schedule that works best for you.",
    ]
    if draft.get("notes"):
        lines += ["", f"Additional details:", draft["notes"]]
    lines += [
        "",
        "Thank you for your time. I look forward to your response.",
        "",
        "Respectfully,",
        p["name"],
    ]
    return "\n".join(lines)


def build_draft():
    """Assemble the email draft payload from the latest booking selection.

    Date/time/place/modality always come from the schedule-tab session state
    (single source of truth) so the calendar and email can never disagree.
    """
    p = st.session_state.profile
    d = st.session_state.get("draft_email") or {}
    advisor = d.get("advisor") or st.session_state.get("selected_advisor") or p.get("advisor", "Your Advisor")
    entry = find_advisor_entry(advisor) or {}
    return {
        "advisor": advisor,
        "to": d.get("email") or entry.get("email") or _advisor_email(advisor),
        "date": _fmt(st.session_state.get("selected_date") or date.today()),
        "time": st.session_state.get("selected_time", "9:00 AM"),
        "place": st.session_state.get("selected_place", "Google Meet"),
        "modality": st.session_state.get("selected_modality", "Online"),
        "topic": d.get("topic") or DEFAULT_TOPIC,
        "notes": d.get("notes") or "",
    }


def prepare_email_draft(draft):
    """Reset the email widget state from a booking selection (call before showing the tab)."""
    st.session_state.email_mode = "preview"
    st.session_state.email_sent = False
    st.session_state.email_to = draft["to"]
    st.session_state.email_subject = f"Consultation Request — {draft['topic']}"
    st.session_state.email_body = _compose_body(draft)


def _render_preview(draft):
    p = st.session_state.profile
    to = st.session_state.get("email_to", draft["to"])
    subject = st.session_state.get("email_subject", f"Consultation Request — {draft['topic']}")
    body = st.session_state.get("email_body", _compose_body(draft))

    st.markdown(f"""
    <div style="border:1.5px solid #DDE2DF; border-radius:14px; padding:1.1rem 1.25rem; background:#FBFCFB;">
        <div style="font-size:0.85rem; margin-bottom:10px;">
            <p style="margin:2px 0;"><b>From:</b> {html.escape(p['name'])} &lt;{html.escape(_student_email())}&gt;</p>
            <p style="margin:2px 0;"><b>To:</b> {html.escape(draft['advisor'])} &lt;{html.escape(to)}&gt;</p>
            <p style="margin:2px 0;"><b>Subject:</b> {html.escape(subject)}</p>
            <p style="margin:2px 0;"><b>When:</b> {html.escape(draft['date'])} at {html.escape(draft['time'])}</p>
            <p style="margin:2px 0;"><b>Where:</b> {html.escape(draft['modality'])} — {html.escape(draft['place'])}</p>
        </div>
        <hr style="border:1px solid #DDE2DF; margin:8px 0 12px;">
        <p style="white-space:pre-wrap; font-size:0.9rem; line-height:1.6;">{html.escape(body)}</p>
    </div>
    """, unsafe_allow_html=True)


def _render_editor(draft):
    p = st.session_state.profile
    st.markdown(f"<p class='muted' style='margin:0;'>From: {html.escape(p['name'])} &lt;{html.escape(_student_email())}&gt;</p>",
                unsafe_allow_html=True)
    st.text_input("To", key="email_to")
    st.text_input("Subject", key="email_subject")
    st.text_area("Message", key="email_body", height=280)
    st.markdown(
        f"<p class='muted' style='margin:0;'>Meeting: <b>{html.escape(draft['date'])}</b> at "
        f"<b>{html.escape(draft['time'])}</b> · <b>{html.escape(draft['modality'])}</b> · "
        f"<b>{html.escape(draft['place'])}</b> — set on the Schedule tab.</p>",
        unsafe_allow_html=True)


def _send_email(draft):
    st.session_state.bookings.append({
        "type": "email",
        "advisor": draft["advisor"],
        "date": draft["date"],
        "time": draft["time"],
        "place": draft.get("place", ""),
        "modality": draft.get("modality", ""),
        "to": st.session_state.get("email_to", draft["to"]),
        "subject": st.session_state.get("email_subject", ""),
        "body": st.session_state.get("email_body", ""),
        "status": "sent",
    })
    st.session_state.email_mode = "preview"
    st.session_state.email_sent = True
    st.rerun()


def render_email_mockup():
    draft = build_draft()
    mode = st.session_state.get("email_mode", "preview")

    st.markdown("<h3 style='margin:0 0 4px;'>New Message</h3>", unsafe_allow_html=True)
    st.markdown("<p class='muted' style='margin-top:0;'>Draft consultation email — review, edit, then send.</p>",
                unsafe_allow_html=True)

    if st.session_state.get("email_sent"):
        st.success("Email sent! (This is a mockup — no email actually went out.)")

    with st.container(border=True):
        if mode == "edit":
            _render_editor(draft)
        else:
            _render_preview(draft)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        c_edit, c_send = st.columns(2)
        with c_edit:
            if st.button("Edit Draft", key="email_edit_btn", type="secondary", width="stretch"):
                st.session_state.email_mode = "edit"
                st.rerun()
        with c_send:
            if st.button("Send Email", key="email_send_btn", type="primary", width="stretch"):
                _send_email(draft)
