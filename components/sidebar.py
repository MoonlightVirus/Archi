import streamlit as st
from styles import SIDEBAR_TOP, SIDEBAR_BOTTOM, SIDEBAR_TEXT_MUTED, WHITE
from state import go, new_chat
from components.settings_modal import render_settings_dialog


def _inject_sidebar_css():
    st.markdown(f"""
    <style>
    /* ---------------- 1. Sidebar Header & Collapse Toggle Fix ---------------- */
    [data-testid="stSidebarHeader"] {{
        padding: 0.2rem 0.6rem 0rem 0.6rem !important;
        background: transparent !important;
        min-height: auto !important;
        position: relative !important;
        z-index: 1000 !important;
        pointer-events: none !important;
    }}

    /* Hide extra native logo image inside header container */
    [data-testid="stSidebarHeader"] img,
    [data-testid="stSidebarHeader"] [data-testid="stLogo"] {{
        display: none !important;
    }}

    /* Collapse toggle button hitbox fix */
    [data-testid="stSidebarHeader"] button,
    [data-testid="stSidebarCollapseButton"] {{
        pointer-events: auto !important;
        position: relative !important;
        z-index: 1001 !important;
    }}

    /* Material Icon font preservation for toggle */
    [data-testid="stSidebarHeader"] button *,
    [data-testid="stSidebarCollapseButton"] *,
    [data-testid="stIcon"],
    .material-symbols-outlined,
    .material-icons {{
        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons', sans-serif !important;
        color: {WHITE} !important;
        fill: {WHITE} !important;
    }}

    /* ---------------- 2. Sidebar Body & Layout ---------------- */
    [data-testid="stSidebarUserContent"] {{
        padding: 0rem 1rem 1rem 1rem !important;
        margin-top: -3.5rem !important;
        position: relative !important;
        z-index: 1 !important;
        overflow: visible !important;
    }}

    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {SIDEBAR_TOP} 0%, {SIDEBAR_BOTTOM} 100%) !important;
    }}

    /* Font application */
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] button,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] input {{
        font-family: 'Glacial Indifference', sans-serif !important;
        color: {WHITE};
    }}

    /* Logo Title */
    .logo-title-text {{
        font-size: 1.6rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px;
        line-height: 1;
        margin: 0;
        display: inline-block;
    }}
    .logo-title-text .green {{ color: #3FE67D !important; }}
    .logo-title-text .white {{ color: #FFFFFF !important; }}

    /* ---------------- 3. Navigation Items ---------------- */
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {{
        gap: 10px !important;
        align-items: center !important;
    }}

    /* Unclip parent element containers */
    [data-testid="stSidebar"] [data-testid="stElementContainer"]:has(.nav-icon-col),
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
        overflow: visible !important;
    }}

    /* Expanded Container for Nav Row Highlight */
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:has(.nav-icon-col) {{
        padding: 0px 10px 0px 1.5rem !important;
        margin-left: -2.5rem !important;
        margin-right: -3.5rem !important;         
        width: calc(100% + 3rem) !important;      
        max-width: none !important;
        border-radius: 0px 20px 20px 0px !important; 
        transition: background 0.2s ease, box-shadow 0.2s ease !important;
        margin-bottom: -15px !important;
    }}

    /* Hover & Active Gradient Highlight for Nav Items */
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:has(.nav-icon-col):hover,
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:has(.active-nav-icon) {{
        background: linear-gradient(90deg, rgba(8, 38, 20, 0.75) 0%, rgba(63, 230, 125, 0.45) 25%, rgba(8, 38, 20, 0.75) 100%) !important;
        box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.15), 0 3px 8px rgba(0, 0, 0, 0.25) !important;
        cursor: pointer !important;
    }}

    .nav-icon-col {{
        width: 34px !important;
        display: flex;
        align-items: center;
        justify-content: center;
    }}

    .nav-icon-col img {{
        width: 34px !important;
        height: 34px !important;
        max-width: 34px !important;
        max-height: 34px !important;
        object-fit: contain !important;
        display: block;
    }}

    /* Left-aligned navigation buttons */
    [data-testid="stSidebar"] button,
    [data-testid="stSidebar"] button p,
    [data-testid="stSidebar"] button div,
    [data-testid="stSidebar"] button span {{
        text-align: left !important;
        justify-content: flex-start !important;
    }}

    [data-testid="stSidebar"] div.stButton > button {{
        background: transparent !important;
        color: {WHITE} !important;
        text-align: left !important;
        justify-content: flex-start !important;
        display: flex !important;
        align-items: center !important;
        border: none !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        padding: 0.15rem 0rem !important;
        box-shadow: none !important;
        width: 100% !important;
    }}

    /* Divider Lines */
    [data-testid="stSidebar"] hr {{
        border: 1px solid rgba(255, 255, 255) !important;
        margin: 10px -15px !important;
        margin-bottom: 15px !important;
    }}

    /* ---------------- 4. Recent Chats Outline Box & Overflow Scroll ---------------- */
    [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stSidebar"] [data-testid="stBorderContainer"] {{
        border: 1.5px solid rgba(255, 255, 255, 0.85) !important;
        border-radius: 16px !important;
        padding: 6px 4px !important;
        background: transparent !important;
        max-height: 360px !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
    }}

    /* Custom Scrollbar for Recent Chats Container */
    [data-testid="stSidebar"] [data-testid="stBorderContainer"]::-webkit-scrollbar {{
        width: 5px !important;
    }}
    [data-testid="stSidebar"] [data-testid="stBorderContainer"]::-webkit-scrollbar-track {{
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 8px !important;
    }}
    [data-testid="stSidebar"] [data-testid="stBorderContainer"]::-webkit-scrollbar-thumb {{
        background: rgba(63, 230, 125, 0.4) !important;
        border-radius: 8px !important;
    }}
    [data-testid="stSidebar"] [data-testid="stBorderContainer"]::-webkit-scrollbar-thumb:hover {{
        background: rgba(63, 230, 125, 0.75) !important;
    }}

    /* Reduce vertical gap between buttons inside Recent Chats block */
    [data-testid="stSidebar"] [data-testid="stBorderContainer"] div[data-testid="stVerticalBlock"] {{
        gap: -5rem !important;
    }}

    /* Hide marker tag containers */
    [data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.recent-chats-marker),
    [data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.profile-avatar-marker),
    [data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.logout-col-marker) {{
        display: none !important;
    }}

    /* Lower vertical margins for each recent chat item container */
    [data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.recent-chats-marker) ~ div[data-testid="stElementContainer"] {{
        margin-bottom: -15px !important;
        margin-left: -2rem !important;
        padding-bottom: 0px !important;
    }}

    /* Recent Chat Buttons Base Layout */
    [data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.recent-chats-marker) ~ div[data-testid="stElementContainer"] div.stButton > button {{
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        padding: 0.45rem 0.85rem !important;
        border-radius: 12px !important;
        transition: all 0.2s ease-in-out !important;
        background: transparent !important;
        border: 1px solid transparent !important;
        width: calc(100% + 3rem) !important;
        margin: 0 !important;
    }}

    /* Hover State FOR RECENT CHATS ONLY */
    [data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.recent-chats-marker) ~ div[data-testid="stElementContainer"] div.stButton > button:hover {{
        background: rgba(63, 230, 125, 0.2) !important;
        box-shadow: inset 0 0 4px rgba(63, 230, 125, 0.2) !important;
        cursor: pointer !important;
    }}

    [data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.recent-chats-marker) ~ div[data-testid="stElementContainer"] div.stButton > button:hover,
    [data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.recent-chats-marker) ~ div[data-testid="stElementContainer"] div.stButton > button:hover p,
    [data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.recent-chats-marker) ~ div[data-testid="stElementContainer"] div.stButton > button:hover span {{
        color: #3FE67D !important;
        font-weight: 700 !important;
    }}

    /* ---------------- 5. Bottom Profile & Logout Section ---------------- */
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:has(.profile-avatar-marker) {{
        background: transparent !important;
        padding: 1rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        margin-top: 0.5rem !important;
    }}

    [data-testid="stSidebar"] [data-testid="stColumn"]:has(.profile-avatar-marker) {{
        display: flex !important;
        margin-left: -1.9rem !important;
        align-items: center !important;
        justify-content: center !important;
    }}

    [data-testid="stSidebar"] [data-testid="stColumn"]:has(.profile-avatar-marker) img {{
        width: 38px !important;
        height: 38px !important;
        max-width: 38px !important;
        max-height: 38px !important;
        border-radius: 50% !important;
        object-fit: cover !important;
        display: block !important;
        margin: 0 !important;
    }}

    .profile-text-container {{
        display: flex !important;
        margin-bottom: 10px !important;
        margin-left: -5px !important;
        flex-direction: column !important;
        justify-content: center !important;
        line-height: 1.2 !important;
        background: transparent !important;
    }}

    .profile-name {{
        margin: 0 !important;
        font-weight: 800 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.3px !important;
        color: #FFFFFF !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }}

    .profile-role {{
        margin: 0 !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        color: #3FE67D !important;
    }}

    /* Column 3 Logout Button Container */
    [data-testid="stSidebar"] [data-testid="stColumn"]:has(.logout-col-marker) {{
        display: flex !important;
        align-items: center !important;
        justify-content: flex-end !important;
    }}

    /* Turn Streamlit button directly into the enlarged logout icon */
    [data-testid="stSidebar"] [data-testid="stColumn"]:has(.logout-col-marker) div.stButton > button {{
        background: transparent url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" height="30px" viewBox="0 -960 960 960" width="30px" fill="%23FFFFFF"><path d="M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h280v80H200v560h280v80H200Zm440-160-55-58 102-102H360v-80h327L585-622l55-58 200 200-200 200Z"/></svg>') no-repeat center center !important;
        background-size: 28px 28px !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        outline: none !important;
        width: 36px !important;
        height: 36px !important;
        min-height: 36px !important;
        padding: 0 !important;
        margin: 0 !important;
        margin-left: 1.5rem !important;
        cursor: pointer !important;
        transition: transform 0.2s ease, opacity 0.2s ease !important;
    }}

    /* Hover effect */
    [data-testid="stSidebar"] [data-testid="stColumn"]:has(.logout-col-marker) div.stButton > button:hover {{
        transform: scale(1.1) !important;
        opacity: 0.85 !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}

    /* Focus & Active states */
    [data-testid="stSidebar"] [data-testid="stColumn"]:has(.logout-col-marker) div.stButton > button:focus,
    [data-testid="stSidebar"] [data-testid="stColumn"]:has(.logout-col-marker) div.stButton > button:active,
    [data-testid="stSidebar"] [data-testid="stColumn"]:has(.logout-col-marker) div.stButton > button:focus-visible {{
        background-color: transparent !important;
        border: none !important;
        border-color: transparent !important;
        box-shadow: none !important;
        outline: none !important;
    }}
    </style>
    """, unsafe_allow_html=True)


def nav_item(label, icon_file, key, is_active=False):
    c1, c2 = st.columns([0.12, 1], vertical_alignment="center")
    active_cls = "active-nav-icon" if is_active else ""
    with c1:
        st.markdown(f'<div class="nav-icon-col {active_cls}">', unsafe_allow_html=True)
        st.image(icon_file)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        res = st.button(label, key=key, width="stretch")
    return res


def render_sidebar():
    _inject_sidebar_css()
    with st.sidebar:
        # Top Logo Header
        c_logo, c_title = st.columns([0.22, 0.78], vertical_alignment="center")
        with c_logo:
            try:
                st.image("images/Logo_white.png", width=34)
            except Exception:
                st.image("images/Logo_green.png", width=34)
        with c_title:
            st.markdown('<span class="logo-title-text"><span class="green">ARC</span><span class="white">HI</span></span>', unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        # New Chat
        if nav_item("New Chat", "images/New.png", "nav_new_chat"):
            new_chat()

        # Navigation Menu
        nav_items = [
            ("dashboard", "Dashboard", "images/Home.png"),
            ("chats_list", "Chats", "images/Chats.png"),
            ("book_consultation", "Book a Consultation", "images/Book.png"),
        ]
        for key, label, icon in nav_items:
            active = st.session_state.get("page") == key
            if nav_item(label, icon, f"nav_{key}", active):
                go(key)

        # Settings
        if nav_item("Settings", "images/Settings.png", "nav_settings"):
            render_settings_dialog()

        st.markdown("<hr>", unsafe_allow_html=True)

        # Recent Chats Section
        st.markdown("<p style='font-size:1.1rem; font-weight:800; margin:0 0 -10px -1rem;'>Recent Chats</p>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown('<div class="recent-chats-marker"></div>', unsafe_allow_html=True)
            
            query = st.session_state.get("chat_search", "").strip().lower()
            for chat_id, chat in st.session_state.get("chats", {}).items():
                if query and query not in chat["title"].lower():
                    continue
                if st.button(chat["title"], key=f"chat_btn_{chat_id}", width="stretch"):
                    st.session_state.active_chat_id = chat_id
                    go("chat")

        st.markdown("<hr>", unsafe_allow_html=True)

        # Bottom Profile & Logout
        p = st.session_state.get("profile", {"name": "Juan De La Cruz", "role": "Student"})
        c1, c2, c3 = st.columns([0.22, 0.65, 0.17], vertical_alignment="center")
        with c1:
            st.markdown('<div class="profile-avatar-marker"></div>', unsafe_allow_html=True)
            st.image("images/profile.png")
        with c2:
            st.markdown(f"""
            <div class="profile-text-container">
                <p class="profile-name">{p['name'].upper()}</p>
                <p class="profile-role">{p['role']}</p>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="logout-col-marker"></div>', unsafe_allow_html=True)
            if st.button("", key="logout_btn", width="stretch"):
                st.session_state.logged_in = False
                st.session_state.auth_view = "login"
                st.rerun()