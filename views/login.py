import streamlit as st

def render_login():
    st.markdown("<div style='height:6vh'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([3, 1.5, 3])
    with col2:
        st.image("images/Logo_green.png", width="stretch")
        st.markdown("""
        <div style="text-align:center;">
            <p class="muted" style="letter-spacing:1.5px; margin-top:10px;">INTELLIGENT ACADEMIC GUIDE</p>
        </div>
        """, unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown('<div class="archi-card" style="margin-top:24px;">', unsafe_allow_html=True)
        st.markdown("<h3 style='margin-top:0;'>Welcome back</h3>", unsafe_allow_html=True)
        st.markdown("<p class='muted'>Login to continue your academic journey.</p>", unsafe_allow_html=True)

        with st.form("login_form"):
            st.text_input("Student ID / Email", value="juan.delacruz@dlsu.edu.ph")
            st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", width="stretch")
            if submitted:
                st.session_state.logged_in = True
                st.session_state.page = "dashboard"
                st.rerun()

        st.caption("Demo login — any credentials will sign you in.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<p style='text-align:center;' class='muted'>Don't have an account?</p>", unsafe_allow_html=True)
        
        # We don't need the extra div wrapper if use_container_width handles the width
        if st.button("Register", key="goto_register", width="stretch"):
            st.session_state.auth_view = "register"
            st.rerun()