import streamlit as st
from state import go, new_chat

def render_dashboard():
    p = st.session_state.profile
    st.markdown("<div style='height:8vh'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="text-align:center;">
        <h1 style="font-size:2.4rem; margin-bottom:6px;">WELCOME, {p['name'].upper()}!</h1>
        <p class="muted" style="font-size:1.05rem;">
            How can I assist you with your academic journey,<br>{p['name']}?
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    
    # Adjusted column ratios to control the width of the buttons
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        # Added type="primary" to pull the dark green style
        if st.button("BOOK A CONSULTATION", key="dash_book", type="primary", width="stretch"):
            go("book_consultation")

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        if st.button("CHAT WITH ARCHI", key="dash_chat", type="primary", width="stretch"):
            new_chat()  