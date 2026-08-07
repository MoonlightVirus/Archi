"""
Shared design tokens + global CSS for ARCHI.
"""

import streamlit as st

# DESIGN TOKENS
WHITE          = "#FFFFFF"
PAGE_BG        = "#FFFFFF"

SIDEBAR_TOP    = "#1E4A34"
SIDEBAR_BOTTOM = "#0E2A1B"
SIDEBAR_ACTIVE = "#2C6B4A"

DARK_GREEN     = "#003B26" 
DARK_GREEN_2   = "#1B4332"
ACCENT         = "#3FE67D"   
ACCENT_DARK    = "#1FAE5C"

TEXT_MAIN      = "#14301F"
TEXT_MUTED     = "#6B8577"
SIDEBAR_TEXT_MUTED = "#9FC2AC"

CARD_GRAY      = "#EBEDEC"
CARD_GRAY_DARK = "#E1E4E2"
BORDER_GRAY    = "#DDE2DF"

BUBBLE_ASSISTANT_FROM = "#A9C2AD"
BUBBLE_ASSISTANT_TO   = "#5F7A66"
BUBBLE_USER           = "#1B4332"

FONT_DISPLAY = "'Glacial Indifference', sans-serif"
FONT_BODY    = "'Glacial Indifference', sans-serif"


def inject_global_css():
    st.markdown(f"""
    <style>

    /* ---------------- Custom Font ---------------- */
    @font-face {{
        font-family: 'Glacial Indifference';
        src: url('/app/static/GlacialIndifference-Regular.otf') format('opentype');
        font-weight: 400;
        font-style: normal;
    }}
    @font-face {{
        font-family: 'Glacial Indifference';
        src: url('/app/static/GlacialIndifference-Bold.otf') format('opentype');
        font-weight: 700;
        font-style: normal;
    }}

    html, body, [class*="css"], p, div, input, textarea, label {{
        font-family: 'Glacial Indifference', sans-serif !important;
        font-weight: 400;
    }}
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Glacial Indifference', sans-serif !important;
        font-weight: 700 !important;
    }}

    /* ----------------  PAGE CONTAINER WIDTH ---------------- */
    .stMainBlockContainer, 
    [data-testid="stMainBlockContainer"], 
    .block-container {{
        max-width: 1200px !important;
        width: 100% !important;
        padding-top: 2rem !important;
        padding-bottom: 5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }}

    /* Preserve Icons */
    [data-testid="stIcon"], 
    .material-symbols-outlined, 
    [class*="Material"], 
    [data-testid="stHeader"] button *,
    [data-testid="stTextInput"] button * {{
        font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
    }}

    #MainMenu, footer {{ visibility: hidden; }}
    [data-testid="stHeader"] {{
        background-color: transparent !important;
        z-index: 999999;
    }}

    h1, h2, h3 {{
        font-family: {FONT_DISPLAY};
        font-weight: 800;
        color: {DARK_GREEN};
        letter-spacing: 0.3px;
    }}

    p, label, .stMarkdown, span {{ color: {TEXT_MAIN}; }}
    .muted {{ color: {TEXT_MUTED} !important; font-size: 0.9rem; }}

    /* ----------------  PREVENT ALL VERTICAL TEXT WRAPPING ON BUTTONS ---------------- */
    button *, 
    button p, 
    button span, 
    button div {{
        white-space: nowrap !important;
        word-break: normal !important;
        word-wrap: normal !important;
        overflow: visible !important;
    }}

    /* Primary pill buttons */
    /* Wax: Add Professor / Save Changes use st.form_submit_button, which renders
       `kind="primaryFormSubmit"` (not `kind="primary"`) — see book_consultation.py. */
    /* Form-submit buttons render `kind="primaryFormSubmit"` (not `kind="primary"`),
       so they need their own selectors to get the white-on-green pill look. */
    button[kind="primary"],
    button[kind="primaryFormSubmit"],
    button[data-testid="stBaseButton-primary"],
    button[data-testid="stBaseButton-primaryFormSubmit"] {{
        background-color: {DARK_GREEN} !important;
        border-radius: 999px !important;
        border: none !important;
        padding: 0.65rem 1.2rem !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    }}
    button[kind="primary"] p, button[kind="primary"] span, button[kind="primary"] div,
    button[kind="primaryFormSubmit"] p, button[kind="primaryFormSubmit"] span, button[kind="primaryFormSubmit"] div,
    button[data-testid="stBaseButton-primary"] p,
    button[data-testid="stBaseButton-primary"] span,
    button[data-testid="stBaseButton-primary"] div,
    button[data-testid="stBaseButton-primaryFormSubmit"] p,
    button[data-testid="stBaseButton-primaryFormSubmit"] span,
    button[data-testid="stBaseButton-primaryFormSubmit"] div {{
        color: {WHITE} !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
    }}

    /* ----------------  CALENDAR & GRID BUTTONS ---------------- */
    /* Target all buttons rendered inside grid columns */
    [data-testid="stColumn"] div[data-testid="stButton"] > button {{
        padding: 0 !important;
        min-height: 40px !important;
        height: 40px !important;
        width: 100% !important;
        border-radius: 10px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}

    /* Override calendar selected (primary) button shape inside columns */
    [data-testid="stColumn"] div[data-testid="stButton"] > button[kind="primary"] {{
        border-radius: 10px !important;
        padding: 0 !important;
    }}

    /* Calendar Day Text formatting */
    [data-testid="stColumn"] div[data-testid="stButton"] > button * {{
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        line-height: 1 !important;
        margin: 0 !important;
    }}

    /* ---------------- Sidebar ---------------- */
    [data-testid="stSidebar"] div.stButton > button {{
        background: transparent !important;
        border: none !important;
        color: white !important;
        text-align: left !important;
        justify-content: flex-start !important;
        padding: 0.2rem 0 !important;
        box-shadow: none !important;
    }}

    /* ---------------- Disabled Button Styling ---------------- */
    button:disabled,
    button[disabled] {{
        background-color: #F2F4F3 !important;
        border: 1px solid #DDE2DF !important;
        opacity: 0.75 !important;
        cursor: not-allowed !important;
        box-shadow: none !important;
    }}
    button:disabled p,
    button:disabled span,
    button:disabled div {{
        color: #7A9384 !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
    }}

    hr {{ border-color: {BORDER_GRAY}; }}

    /* ---------------- Modal / Dialog Buttons ---------------- */

    /* Primary Button (Confirm Booking) inside Dialog */
    div[data-testid="stDialog"] button[kind="primary"],
    div[role="dialog"] button[kind="primary"],
    div[data-testid="stDialog"] button[data-testid="stBaseButton-primary"] {{
        background: linear-gradient(135deg, #1C5233 0%, #123B23 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        padding: 0.5rem 1.25rem !important;
        margin-left: 2.5rem !important;
        width: calc(100% + 1rem) !important;
        box-shadow: 0 4px 12px rgba(28, 82, 51, 0.25) !important;
        transition: all 0.2s ease !important;
    }}

    div[data-testid="stDialog"] button[kind="primary"]:hover,
    div[role="dialog"] button[kind="primary"]:hover {{
        background: linear-gradient(135deg, #21633D 0%, #16472A 100%) !important;
        color: #FFFFFF !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 16px rgba(28, 82, 51, 0.35) !important;
    }}

    /* Secondary Button (Cancel) inside Dialog */
    div[data-testid="stDialog"] button[kind="secondary"],
    div[role="dialog"] button[kind="secondary"],
    div[data-testid="stDialog"] button[data-testid="stBaseButton-secondary"] {{
        background: #EBF0EC !important;
        color: #0D381E !important;
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        padding: 0.5rem 1.25rem !important;
    }}

    div[data-testid="stDialog"] button[kind="secondary"]:hover,
    div[role="dialog"] button[kind="secondary"]:hover {{
        background: #DEE5E0 !important;
        border-color: #21633D !important;
    }}
    
    </style>
    """, unsafe_allow_html=True)