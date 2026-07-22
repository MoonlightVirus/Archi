import streamlit as st

def render_register():
    st.markdown("<div style='height:6vh'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([3, 1.5, 3])
    with col2:
        st.image("images/Logo_green.png", use_container_width=True)
        st.markdown("""
        <div style="text-align:center;">
            <p class="muted" style="letter-spacing:1.5px; margin-top:-15px;">INTELLIGENT ACADEMIC GUIDE</p>
        </div>
        """, unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown('<div class="archi-card" style="margin-top:24px;">', unsafe_allow_html=True)
        st.markdown("<h3 style='margin-top:0;'>Create your account</h3>", unsafe_allow_html=True)
        st.markdown("<p class='muted'>Register to get real-time academic guidance.</p>", unsafe_allow_html=True)

        with st.form("register_form"):
            full_name = st.text_input("Full name")
            st.text_input("Student ID / Email")
            program = st.selectbox("Program", ["BSCS", "BSIT", "BSIS", "BSCPE", "Other"])
            st.text_input("Password", type="password")
            st.text_input("Confirm password", type="password")
            
            # Stretch the submit button
            submitted = st.form_submit_button("Create Account", use_container_width=True)
            if submitted:
                if full_name.strip():
                    st.session_state.profile["name"] = full_name.strip()
                st.session_state.profile["program"] = program
                st.session_state.logged_in = True
                st.session_state.page = "dashboard"
                st.rerun()

        st.caption("Demo registration — no data is sent anywhere yet.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<p style='text-align:center;' class='muted'>Already have an account?</p>", unsafe_allow_html=True)
        
        # Stretch the bottom button
        if st.button("Back to Login", key="goto_login", use_container_width=True):
            st.session_state.auth_view = "login"
            st.rerun()