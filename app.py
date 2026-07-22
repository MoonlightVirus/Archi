"""
ARCHI — Intelligent Academic Guide
Streamlit frontend built from the ARCHI Website Mockup Design.

Run with:  streamlit run app.py
"""

import streamlit as st

from state import init_session_state
from styles import inject_global_css

from views.login import render_login
from views.register import render_register
from views.dashboard import render_dashboard
from views.chat import render_chat
from views.chats_list import render_chats_list
from views.book_consultation import render_book_consultation
from components.sidebar import render_sidebar

st.set_page_config(
    page_title="ARCHI | Intelligent Academic Guide",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()
inject_global_css()

if not st.session_state.logged_in:
    st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
    if st.session_state.auth_view == "register":
        render_register()
    else:
        render_login()
else:
    st.logo(
        "images/Logo_white.png", 
        icon_image="images/Logo_green.png"
    )
    
    render_sidebar()
    PAGE_MAP = {
        "dashboard": render_dashboard,
        "chat": render_chat,
        "chats_list": render_chats_list,
        "book_consultation": render_book_consultation,
    }
    PAGE_MAP.get(st.session_state.page, render_dashboard)()
