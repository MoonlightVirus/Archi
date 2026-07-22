import streamlit as st
import base64
import os
import html
import time

def get_image_base64(image_path):
    """Reads a local image and converts it to a base64 string for CSS injection."""
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode()
            return f"data:image/png;base64,{encoded_string}"
    return ""

def _inject_chat_css():
    upload_icon_b64 = get_image_base64("images/Upload.png")
    send_icon_b64 = get_image_base64("images/Send.png")

    st.markdown(f"""
    <style>
    /* ---------------- 1. Main Container Layout ---------------- */
    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 120px !important;
        max-width: 920px !important;
    }}

    /* ---------------- 2. Sticky Top Header Layout ---------------- */
    .chat-header-title {{
        display: inline !important;
        background: #FFFFFF !important;
        width: 70% !important;
        right: 5% !important;
        text-align: left !important;
        position: fixed !important;
        top: 0 !important;   
        margin: 0 !important;
        padding: 1rem !important;
        font-size: 1.65rem !important;
        font-weight: 800 !important;
        color: #0D381E !important;
        line-height: 1.2 !important;
        text-transform: uppercase !important;
        z-index: 1001 !important;
    }}

    div[data-testid="stColumn"]:nth-child(2) div[data-testid="stPopover"] {{
        float: right !important;
    }}
                
    div[data-testid="stPopover"] {{
        position: fixed !important;
        top: 4rem !important;
        max-width: 140px !important;
        right: 1rem !important;
        z-index: 1002 !important;
    }}

    div[data-testid="stPopover"] > button {{
        background: #EBF0EC !important;
        border: 1px solid rgba(0, 0, 0, 0.08) !important;
        border-radius: 12px !important;
        color: #0D381E !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        padding: 0.4rem 1rem !important;
        max-width: 140px !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.2s ease !important;
        margin: 0 !important;
        z-index: 1002 !important;
    }}

    div[data-testid="stPopoverBody"] {{
        padding: 8px !important;
        border-radius: 12px !important;
        max-width: 140px !important;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15) !important;
        z-index: 1002 !important;
    }}

    /* ---------------- 3. Chat Messages Layout & Spacing ---------------- */
    .messages-container {{
        display: flex;
        flex-direction: column;
        width: 100%;
        margin-top: 0.5rem;
    }}

    .msg-assistant-row {{
        display: flex;
        justify-content: flex-start;
        width: 100%;
        margin-bottom: 1.25rem !important;
    }}

    .msg-assistant-bubble {{
        background: linear-gradient(135deg, #A2B8AA 0%, #8AA393 100%);
        color: #0C1E13;
        font-weight: 600;
        font-size: 0.95rem;
        padding: 1rem 1.35rem;
        border-radius: 20px 20px 20px 4px;
        max-width: 70%;
        box-shadow: 0px 8px 20px rgba(0, 0, 0, 0.2);
        line-height: 1.5;
        white-space: pre-wrap;
        word-break: break-word;
    }}

    .msg-user-row {{
        display: flex;
        justify-content: flex-end;
        width: 100%;
        margin-bottom: 1.25rem !important;
    }}

    .msg-user-bubble {{
        background: linear-gradient(135deg, #1C5233 0%, #123B23 100%);
        color: #FFFFFF !important;
        font-weight: 600;
        font-size: 0.95rem;
        padding: 1rem 1.35rem;
        border-radius: 20px 20px 4px 20px;
        max-width: 70%;
        box-shadow: 0px 8px 20px rgba(0, 0, 0, 0.25);
        line-height: 1.5;
        white-space: pre-wrap;
        word-break: break-word;
    }}

    /* Crisp White Text & Icon for Uploaded File Bubbles */
    .msg-file-bubble {{
        background: linear-gradient(135deg, #1C5233 0%, #123B23 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.4px !important;
        padding: 0.85rem 1.3rem !important;
        border-radius: 18px !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 10px !important;
        box-shadow: 0px 8px 20px rgba(0, 0, 0, 0.25) !important;
    }}

    .msg-file-bubble,
    .msg-file-bubble *,
    .msg-file-bubble span {{
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }}

    .msg-file-bubble svg {{
        width: 20px !important;
        height: 20px !important;
        fill: #FFFFFF !important;
        flex-shrink: 0 !important;
    }}

    /* ---------------- 4. Fixed Bottom Form Input Bar ---------------- */
    div[data-testid="stForm"] {{
        position: absolute !important;
        bottom: 35px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: 90% !important;
        max-width: 840px !important;
        height: 60px !important;
        background: linear-gradient(180deg, #E6E8E6 0%, #CDD2CE 100%) !important;
        border: 2px solid #21633D !important;
        border-radius: 12px !important;
        padding: 0.5rem 1.25rem !important;
        box-shadow: 0px 12px 28px rgba(0, 0, 0, 0.38) !important;
        z-index: 99999 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-sizing: border-box !important;
    }}

    div[data-testid="stForm"] > div {{
        width: 100% !important;
        height: 100% !important;
        display: flex !important;
        align-items: center !important;
    }}

    div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] {{
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        gap: 12px !important;
        margin: 0 !important;
        padding: 0 !important;
    }}

    div[data-testid="stForm"] div[data-testid="stColumn"] {{
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
        margin: 0 !important;
        height: auto !important;
        min-width: 0 !important;
    }}

    div[data-testid="stForm"] div[data-testid="stVerticalBlock"] {{
        gap: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        min-width: 0 !important;
    }}

    div[data-testid="stForm"] label {{
        display: none !important;
    }}

    div[data-testid="stForm"] small, 
    [data-testid="stFormInstructions"] {{
        display: none !important;
    }}

    /* File Attach Button */
    [data-testid="stFileUploader"] {{
        width: 38px !important;
        height: 38px !important;
        min-height: 38px !important;
        max-height: 38px !important;
        margin: 0 !important;
        padding: 0 !important;
    }}

    [data-testid="stFileUploader"] section {{
        width: 38px !important;
        height: 38px !important;
        min-height: 38px !important;
        max-height: 38px !important;
        margin: 0 !important;
        padding: 0 !important;
        border: none !important;
        cursor: pointer !important;
        background-color: transparent !important;
        background-image: url('{upload_icon_b64}') !important;
        background-size: cover !important; 
        background-repeat: no-repeat !important;
        background-position: center !important;
    }}

    [data-testid="stFileUploader"] section * {{
        display: none !important;
    }}

    /* Input Box Column Limits */
    div[data-testid="stForm"] div[data-testid="stColumn"]:nth-child(2) {{
        justify-content: flex-start !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }}

    div[data-testid="stForm"] div[data-testid="stTextInput"] {{
        width: 100% !important;
        min-width: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }}

    div[data-testid="stForm"] div[data-baseweb="input"], 
    div[data-testid="stForm"] div[data-baseweb="base-input"] {{
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
        width: 100% !important;
        min-width: 0 !important;
        overflow: hidden !important;
    }}

    div[data-testid="stForm"] input[type="text"] {{
        background-color: transparent !important;
        border: none !important;
        outline: none !important;
        font-weight: 800 !important;
        color: #1C5233 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.5px !important;
        box-shadow: none !important;
        padding: 0 8px !important;
        margin: 0 !important;
        height: 38px !important;
        min-height: 38px !important;
        line-height: 38px !important;
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        white-space: nowrap !important;
    }}

    div[data-testid="stForm"] input[type="text"]::placeholder {{
        color: #267045 !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
        opacity: 0.9 !important;
    }}

    /* Send Button */
    div[data-testid="stFormSubmitButton"] {{
        margin: 0 !important;
        padding: 0 !important;
    }}
    
    div[data-testid="stFormSubmitButton"] button {{
        width: 38px !important;
        height: 38px !important;
        min-height: 38px !important;
        max-height: 38px !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important; 
        transition: transform 0.15s ease !important;
        cursor: pointer !important;
        background-color: transparent !important;
        background-image: url('{send_icon_b64}') !important;
        background-size: cover !important; 
        background-repeat: no-repeat !important;
        background-position: center !important;
    }}

    div[data-testid="stFormSubmitButton"] button p {{
        display: none !important; 
    }}

    div[data-testid="stFormSubmitButton"] button:hover {{
        transform: scale(1.05) !important;
    }}
    </style>
    """, unsafe_allow_html=True)


def render_chat():
    _inject_chat_css()

    chats = st.session_state.get("chats", {})
    active_id = st.session_state.get("active_chat_id")

    if not active_id or active_id not in chats:
        if chats:
            st.session_state.active_chat_id = list(chats.keys())[0]
            active_id = st.session_state.active_chat_id
        else:
            st.info("No active conversation found.")
            return

    current_chat = chats[active_id]
    chat_title = current_chat.get("title", "New Chat")

    # 1. Sticky Top Header
    st.markdown('<div class="chat-header-wrapper">', unsafe_allow_html=True)
    header_left, header_right = st.columns([0.8, 0.2], vertical_alignment="center")

    with header_left:
        st.markdown(f'<h2 class="chat-header-title">{html.escape(chat_title)}</h2>', unsafe_allow_html=True)

    with header_right:
        popover = st.popover("Chat Settings", key="chat_settings_popover")
        with popover:
            if st.button("Delete Chat", key="delete_chat_settings_btn", use_container_width=True):
                del st.session_state.chats[active_id]
                remaining = list(st.session_state.chats.keys())
                st.session_state.active_chat_id = remaining[0] if remaining else None
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # 2. Build Messages HTML
    messages = current_chat.get("messages", [])
    chat_html_parts = ['<div class="messages-container">']

    for msg in messages:
        role = "assistant"
        content = ""
        msg_type = "text"
        file_name = None

        if isinstance(msg, dict):
            role = msg.get("role", "assistant")
            content = msg.get("content", "")
            msg_type = msg.get("type", "text")
            file_name = msg.get("name") or msg.get("filename")
        elif isinstance(msg, (tuple, list)):
            role_or_type = str(msg[0]).lower()
            if role_or_type in ("user", "assistant"):
                role = role_or_type
                content = msg[1] if len(msg) > 1 else ""
            elif role_or_type in ("file", "attachment"):
                role = "user"
                msg_type = "file"
                file_name = msg[1] if len(msg) > 1 else "DOCUMENT.PDF"

        safe_content = html.escape(str(content))
        safe_file_name = html.escape(str(file_name or content))

        if role == "user":
            if msg_type == "file" or (isinstance(content, str) and content.lower().endswith(('.pdf', '.png', '.jpg', '.docx'))):
                chat_html_parts.append(f"""
                <div class="msg-user-row">
                    <div class="msg-file-bubble">
                        <svg viewBox="0 0 24 24"><path d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2ZM18 20H6V4H13V9H18V20Z"/></svg>
                        <span>{safe_file_name.upper()}</span>
                    </div>
                </div>
                """)
            else:
                chat_html_parts.append(f"""
                <div class="msg-user-row">
                    <div class="msg-user-bubble">{safe_content}</div>
                </div>
                """)
        else:
            chat_html_parts.append(f"""
            <div class="msg-assistant-row">
                <div class="msg-assistant-bubble">{safe_content}</div>
            </div>
            """)

    chat_html_parts.append('</div>')

    raw_html = "".join(chat_html_parts)
    clean_html = "\n".join(line.strip() for line in raw_html.splitlines())
    st.markdown(clean_html, unsafe_allow_html=True)

    # 3. Handle Delayed AI Reply
    if st.session_state.get("awaiting_reply"):
        st.session_state.awaiting_reply = False
        with st.spinner("Archi is thinking..."):
            time.sleep(1.2)

        current_chat["messages"].append({
            "role": "assistant",
            "content": "Okay! I understand your situation, allow me to help! Please upload your flowchart first and I will analyze and provide suggestions!"
        })
        st.rerun()

    # 4. Clean Unified Input Form
    with st.form(key="chat_input_form", clear_on_submit=True):
        c_plus, c_input, c_send = st.columns([0.06, 0.88, 0.06], vertical_alignment="center")

        with c_plus:
            uploaded_file = st.file_uploader("Attach", key="chat_file_upload", label_visibility="collapsed")

        with c_input:
            prompt = st.text_input(
                "Prompt",
                placeholder="ASK ARCHI ABOUT ACADEMIC CONCERNS...",
                label_visibility="collapsed",
                key="user_chat_prompt"
            )

        with c_send:
            submitted = st.form_submit_button("Send")

    if submitted:
        has_content = False

        if uploaded_file:
            current_chat.setdefault("messages", []).append({
                "role": "user",
                "type": "file",
                "name": uploaded_file.name
            })
            has_content = True

        if prompt and prompt.strip():
            current_chat.setdefault("messages", []).append({
                "role": "user",
                "content": prompt.strip()
            })
            has_content = True

        if has_content:
            st.session_state.awaiting_reply = True

        st.rerun()