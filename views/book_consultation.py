import calendar
from datetime import date
import streamlit as st
from state import (get_advisors, get_day_bookings, register_advisor, update_advisor,
                   find_advisor_entry, _same_person, MODALITIES, PLACES_BY_MODALITY, TIME_SLOTS)
from components.consultation_modal import render_consultation_dialog
from components.email_mockup import build_draft, prepare_email_draft, render_email_mockup

def _init_calendar_state():
    today = date.today()
    st.session_state.setdefault("cal_year", today.year)
    st.session_state.setdefault("cal_month", today.month)
    st.session_state.setdefault("selected_date", today)
    st.session_state.setdefault("selected_advisor", get_advisors()[0]["name"])
    st.session_state.setdefault("selected_time", "9:00 AM")
    st.session_state.setdefault("selected_modality", "Online")
    st.session_state.setdefault("selected_place", PLACES_BY_MODALITY["Online"][0])

def _render_day_bookings(day_bookings):
    """Compact mini-tab under each day showing its bookings + status."""
    chips = []
    for b in day_bookings[:3]:
        if b["status"] == "Email Sent":
            icon, color = "●", "#1F8A5B"
        elif b["status"] == "Pending":
            icon, color = "◐", "#C48A1D"
        else:
            icon, color = "✕", "#8A8F8C"
        surname = b.get("advisor", "").split()[-1] if b.get("advisor") else "?"
        mod = b.get("modality") or ""
        chips.append(
            f"<span style='color:{color}; font-size:0.62rem; white-space:nowrap;'>"
            f"{icon} {b.get('time', '')} {surname}{' · ' + mod if mod else ''}</span>"
        )
    html = ("<div style='margin-top:2px; display:flex; flex-wrap:wrap; "
            "gap:0 4px; line-height:1.5;'>" + " ".join(chips) + "</div>")
    if len(day_bookings) > 3:
        html += f"<p style='color:#8A8F8C; font-size:0.6rem; margin:0;'>+{len(day_bookings) - 3} more</p>"
    st.markdown(html, unsafe_allow_html=True)


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
            st.markdown(
                "<p class='muted' style='margin:0; font-size:0.82rem;'>◻ Available &nbsp; ◼ Selected &nbsp;|&nbsp; "
                "<span style='color:#1F8A5B'>● Email Sent</span> &nbsp; "
                "<span style='color:#C48A1D'>◐ Pending</span> &nbsp; "
                "<span style='color:#8A8F8C'>✕ Cancelled</span></p>",
                unsafe_allow_html=True)
        with f2:
            st.session_state.selected_time = st.selectbox(
                "Time", 
                TIME_SLOTS, 
                index=TIME_SLOTS.index(st.session_state.selected_time), 
                label_visibility="collapsed"
            )

def _render_advisors():
    st.markdown("<h3 style='margin-top:0;'>Available Advisors</h3>", unsafe_allow_html=True)
    advisors = get_advisors()

    if st.session_state.get("editing_advisor"):
        target = st.session_state.editing_advisor
        advisor = find_advisor_entry(target)
        if advisor:
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown(
                    f"<p style='margin:0 0 4px; font-weight:700;'>Editing: "
                    f"<span class='muted'>{target}</span></p>",
                    unsafe_allow_html=True)
                with st.form(key="edit_advisor_form"):
                    e_name = st.text_input("Professor name", value=advisor["name"], key=f"edit_name_{target}")
                    e_role = st.text_input("Role", value=advisor.get("role", ""), key=f"edit_role_{target}")
                    e_email = st.text_input("Email (optional)", value=advisor.get("email") or "", key=f"edit_email_{target}")
                    e_avail = st.checkbox("Available for consultations", value=bool(advisor.get("available", True)),
                                          key=f"edit_avail_{target}")
                    saved = st.form_submit_button("Save Changes", type="primary", width="stretch")
                if st.button("Cancel", key="cancel_edit_advisor"):
                    del st.session_state.editing_advisor
                    st.rerun()
                if saved:
                    new_name = e_name.strip()
                    if new_name:
                        update_advisor(target, name=new_name, role=e_role.strip(), email=e_email.strip() or None,
                                       available=e_avail)
                        if (not st.session_state.get("email_sent")
                                and _same_person(st.session_state.get("selected_advisor", ""), target)):
                            prepare_email_draft(build_draft())
                            st.session_state.email_mode = "preview"
                        del st.session_state.editing_advisor
                        st.rerun()

    advisors_box = st.container(height=280) if len(advisors) >= 5 else st.container()
    with advisors_box:
        for advisor in advisors:
            selected = advisor["name"] == st.session_state.selected_advisor
            with st.container(border=True):
                c1, c2, c3 = st.columns([2.2, 1.1, 0.8], vertical_alignment="center")
                with c1:
                    email_html = (f"<p class='muted' style='margin:0; font-size:0.72rem;'>{advisor['email']}</p>"
                                  if advisor.get("email") else "")
                    st.markdown(f"""
                    <div style="display:flex; align-items:center; gap:12px;">
                        <div style="width:38px; height:38px; border-radius:50%; background:#DCE6DF;
                                    display:flex; align-items:center; justify-content:center; font-size:1.1rem;">🧑‍🏫</div>
                        <div>
                            <p style="margin:0; font-weight:700; font-size:0.9rem;">{advisor['name']}</p>
                            <p class="muted" style="margin:0; font-size:0.78rem;">{advisor['role']}</p>{email_html}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with c2:
                    if advisor["available"]:
                        label = "✓" if selected else "Select"
                        btn_type = "primary" if selected else "secondary"
                        if st.button(label, key=f"pick_{advisor['name']}", type=btn_type, width="stretch"):
                            _select_advisor(advisor["name"])
                            st.rerun()
                    else:
                        # Disabled button matches the exact dimensions and alignment of active buttons
                        st.button("Unavailable", key=f"disabled_{advisor['name']}", disabled=True, width="stretch")
                with c3:
                    if st.button("Edit", key=f"edit_btn_{advisor['name']}", width="stretch"):
                        for k in (f"edit_name_{advisor['name']}", f"edit_role_{advisor['name']}",
                                  f"edit_email_{advisor['name']}", f"edit_avail_{advisor['name']}"):
                            st.session_state.pop(k, None)
                        st.session_state.editing_advisor = advisor["name"]
                        st.rerun()

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    with st.expander("Add a professor manually", expanded=True):
        with st.form(key="add_professor_form", clear_on_submit=True):
            prof_name = st.text_input("Professor name", placeholder="e.g. Ms. Romualde", key="add_prof_name")
            prof_email = st.text_input("Email (optional)", placeholder="e.g. ms.romualde@dlsu.edu.ph", key="add_prof_email")
            submitted = st.form_submit_button("Add Professor", type="primary", width="stretch")
        if submitted:
            name = prof_name.strip()
            if name:
                register_advisor(name, email=prof_email.strip() or None, role="Added by Student")
                st.rerun()
            else:
                st.error("Please enter a professor name.")

def _render_meeting_details():
    """Modality + place dropdowns — the single source of truth for the email."""
    st.markdown("<h3 style='margin-top:0;'>Meeting Details</h3>", unsafe_allow_html=True)

    modalities = MODALITIES
    mod_index = modalities.index(st.session_state.selected_modality) \
        if st.session_state.selected_modality in modalities else 0
    modality = st.selectbox("Modality", modalities, index=mod_index)
    if modality != st.session_state.selected_modality:
        st.session_state.selected_modality = modality
        st.session_state.selected_place = PLACES_BY_MODALITY[modality][0]
        st.rerun()

    places = PLACES_BY_MODALITY[st.session_state.selected_modality]
    place_index = places.index(st.session_state.selected_place) \
        if st.session_state.selected_place in places else 0
    st.session_state.selected_place = st.selectbox("Place / Venue", places, index=place_index)


def _render_schedule_tab():
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