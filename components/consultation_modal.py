import streamlit as st
from state import TOPIC_OPTIONS
from components.email_mockup import build_draft, prepare_email_draft


@st.dialog("Consultation Details")
def render_consultation_dialog(advisor_name, booking_date, time_slot):
    p = st.session_state.profile

    st.markdown(f"<p class='muted' style='margin-top:-8px;'>With <b>{advisor_name}</b> on {booking_date} at {time_slot}</p>",
                unsafe_allow_html=True)

    topic = st.selectbox("Topic / Concern", TOPIC_OPTIONS)
    notes = st.text_area("Additional Notes", placeholder="Briefly describe what you'd like to discuss...")

    st.markdown(f"""
    <div class="archi-info-box">
        Your current GPA is <b>{p['gpa']:.1f}</b> (Status: {p['status'].title()}).
        Discussing your flowchart is highly recommended for this session.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    col_cancel, col_confirm = st.columns([1, 1])

    with col_cancel:
        if st.button("Cancel", key="modal_cancel_btn", type="secondary"):
            st.rerun()

    with col_confirm:
        # Adding type="primary" ensures it gets the green styling
        if st.button("Confirm Booking", key="modal_confirm_btn", type="primary"):
            st.session_state.draft_email = {
                "advisor": advisor_name,
                "date": booking_date,
                "time": time_slot,
                "topic": topic,
                "notes": notes,
            }
            prepare_email_draft(build_draft())
            st.session_state["book_consultation_tabs"] = 1
            st.rerun()
