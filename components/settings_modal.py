import streamlit as st


@st.dialog("Settings")
def render_settings_dialog():
    p = st.session_state.profile

    st.markdown("<p class='muted' style='margin-top:-8px;'>Basic account preferences.</p>", unsafe_allow_html=True)

    p["name"] = st.text_input("Display name", value=p["name"])
    st.text_input("Email", value=f"{p['name'].lower().replace(' ', '.')}@dlsu.edu.ph", disabled=True)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    st.toggle("Email me about upcoming consultations", value=True, key="settings_notify_email")
    st.toggle("Remind me before flowchart deadlines", value=True, key="settings_notify_deadlines")
    st.toggle("Dark mode", value=False, key="settings_dark_mode", disabled=True,
              help="Coming soon")

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Close"):
            st.rerun()
    with c2:
        if st.button("Save changes"):
            st.success("Settings saved.")
            st.rerun()
