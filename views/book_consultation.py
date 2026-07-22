import calendar
from datetime import date
import streamlit as st
from state import ADVISORS
from components.consultation_modal import render_consultation_dialog

TIME_SLOTS = ["9:30 AM", "10:30 AM", "11:30 AM", "1:00 PM", "2:00 PM", "3:00 PM"]

def _init_calendar_state():
    today = date.today()
    st.session_state.setdefault("cal_year", today.year)
    st.session_state.setdefault("cal_month", today.month)
    st.session_state.setdefault("selected_date", today)
    st.session_state.setdefault("selected_advisor", ADVISORS[0]["name"])
    st.session_state.setdefault("selected_time", TIME_SLOTS[0])

def _render_calendar():
    year, month = st.session_state.cal_year, st.session_state.cal_month

    with st.container(border=True):
        # Header navigation row
        h1, h2, h3 = st.columns([8, 1, 1], vertical_alignment="center")
        with h1:
            st.markdown(f"<h3 style='margin:0;'>{calendar.month_name[month]} {year}</h3>", unsafe_allow_html=True)
        with h2:
            if st.button("‹", key="cal_prev", width="stretch"):
                month -= 1
                if month == 0: month, year = 12, year - 1
                st.session_state.cal_month, st.session_state.cal_year = month, year
                st.rerun()
        with h3:
            if st.button("›", key="cal_next", width="stretch"):
                month += 1
                if month == 13: month, year = 1, year + 1
                st.session_state.cal_month, st.session_state.cal_year = month, year
                st.rerun()

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        
        # Weekday Labels
        weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        cols = st.columns(7)
        for c, wd in zip(cols, weekdays):
            c.markdown(f"<p class='muted' style='text-align:center; font-weight:700; margin:0; font-size:0.88rem;'>{wd}</p>", unsafe_allow_html=True)

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        # Days Grid
        cal = calendar.Calendar(firstweekday=6)
        for week in cal.monthdayscalendar(year, month):
            cols = st.columns(7)
            for c, day in zip(cols, week):
                if day == 0:
                    c.markdown("&nbsp;", unsafe_allow_html=True)
                    continue
                this_date = date(year, month, day)
                is_selected = this_date == st.session_state.selected_date
                btn_type = "primary" if is_selected else "secondary"
                with c:
                    if st.button(str(day), key=f"day_{year}_{month}_{day}", type=btn_type, width="stretch"):
                        st.session_state.selected_date = this_date
                        st.rerun()

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # Bottom row inside calendar container
        f1, f2 = st.columns([2, 1], vertical_alignment="center")
        with f1:
            st.markdown("<p class='muted' style='margin:0; font-size:0.85rem;'>◻ Available &nbsp;&nbsp; ◼ Selected</p>", unsafe_allow_html=True)
        with f2:
            st.session_state.selected_time = st.selectbox(
                "Time", 
                TIME_SLOTS, 
                index=TIME_SLOTS.index(st.session_state.selected_time), 
                label_visibility="collapsed"
            )

def _render_advisors():
    st.markdown("<h3 style='margin-top:0;'>Available Advisors</h3>", unsafe_allow_html=True)
    for advisor in ADVISORS:
        selected = advisor["name"] == st.session_state.selected_advisor
        with st.container(border=True):
            c1, c2 = st.columns([2.2, 1.4], vertical_alignment="center")
            with c1:
                st.markdown(f"""
                <div style="display:flex; align-items:center; gap:12px;">
                    <div style="width:38px; height:38px; border-radius:50%; background:#DCE6DF;
                                display:flex; align-items:center; justify-content:center; font-size:1.1rem;">🧑‍🏫</div>
                    <div>
                        <p style="margin:0; font-weight:700; font-size:0.9rem;">{advisor['name']}</p>
                        <p class="muted" style="margin:0; font-size:0.78rem;">{advisor['role']}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                if advisor["available"]:
                    label = "✓" if selected else "Select"
                    btn_type = "primary" if selected else "secondary"
                    if st.button(label, key=f"pick_{advisor['name']}", type=btn_type, width="stretch"):
                        st.session_state.selected_advisor = advisor["name"]
                        st.rerun()
                else:
                    # Disabled button matches the exact dimensions and alignment of active buttons
                    st.button("Unavailable", key=f"disabled_{advisor['name']}", disabled=True, width="stretch")

def render_book_consultation():
    _init_calendar_state()
    st.markdown("<h2>Book a Consultation</h2>", unsafe_allow_html=True)
    st.markdown("<p class='muted'>Select a date and advisor to schedule your academic advising session.</p>", unsafe_allow_html=True)
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Wide column split across the 1200px container
    left, right = st.columns([1.8, 1.2], gap="large")
    with left:
        _render_calendar()
    with right:
        _render_advisors()
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        if st.button("Consultation Details", key="open_consultation_modal", type="primary", width="stretch"):
            render_consultation_dialog(
                st.session_state.selected_advisor,
                st.session_state.selected_date,
                st.session_state.selected_time,
            )