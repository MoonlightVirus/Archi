import streamlit as st
from state import go


def _extract_last_message(chat):
    """Extract human-readable preview text for chat card subtext."""
    messages = chat.get("messages", [])
    if not messages:
        return "No messages yet."

    last = messages[-1]

    # Plain string case
    if isinstance(last, str):
        if last.strip().lower() in ("text", "file", "image", "doc"):
            return "No text messages yet."
        return last

    # Tuple/List case e.g. ('text', 'Hello') or ('file', 'blueprint.pdf')
    if isinstance(last, (list, tuple)):
        filtered = [
            str(e) for e in last
            if isinstance(e, str) and e.strip().lower() not in ("user", "assistant", "system", "text", "file", "image", "doc")
        ]
        if filtered:
            return filtered[-1]
        if len(last) > 1:
            return str(last[1])
        if len(last) == 1 and str(last[0]).strip().lower() not in ("text", "file"):
            return str(last[0])
        return "No text messages yet."

    # Dict case e.g. {'role': 'user', 'content': 'Hello'}
    if isinstance(last, dict):
        for field in ["content", "text", "message", "body", "prompt", "response"]:
            val = last.get(field)
            if val and isinstance(val, str) and val.strip().lower() not in ("text", "file"):
                return val
            elif val and isinstance(val, (list, tuple)):
                for item in val:
                    if isinstance(item, dict):
                        sub = item.get("text") or item.get("content")
                        if sub and isinstance(sub, str):
                            return sub
                    elif isinstance(item, str):
                        return item

        if "name" in last or "filename" in last:
            filename = last.get("name") or last.get("filename")
            return f"📎 Attachment: {filename}"

        for k, v in last.items():
            if k.lower() not in ("type", "role", "id", "timestamp", "sender") and isinstance(v, str):
                if v.strip().lower() not in ("text", "file"):
                    return v

    return "No messages yet."


def _inject_chats_list_css():
    st.markdown("""
    <style>
    /* Hide Marker Element */
    div[data-testid="stElementContainer"]:has(.chat-card-marker) {
        display: none !important;
    }

    /* ---------------- Chat Card Buttons Styling ---------------- */
    div[data-testid="stElementContainer"]:has(.chat-card-marker) + div[data-testid="stElementContainer"] div.stButton > button {
        width: 100% !important;
        text-align: left !important;
        justify-content: flex-start !important;
        align-items: flex-start !important;
        flex-direction: column !important;
        padding: 0.95rem 1.25rem !important;
        border-radius: 14px !important;
        border: 1.5px solid rgba(180, 180, 180, 0.35) !important;
        background: #ffffff !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02) !important;
        transition: all 0.2s ease-in-out !important;
        margin-bottom: 0.65rem !important;
        min-height: 72px !important;
        height: auto !important;
    }

    /* Hover Effect on Entire Chat Card */
    div[data-testid="stElementContainer"]:has(.chat-card-marker) + div[data-testid="stElementContainer"] div.stButton > button:hover {
        border-color: #3FE67D !important;
        background: rgba(63, 230, 125, 0.06) !important;
        box-shadow: 0 4px 14px rgba(63, 230, 125, 0.2) !important;
        transform: translateY(-2px) !important;
        cursor: pointer !important;
    }

    /* Left align card text & wrap properly */
    div[data-testid="stElementContainer"]:has(.chat-card-marker) + div[data-testid="stElementContainer"] div.stButton > button p,
    div[data-testid="stElementContainer"]:has(.chat-card-marker) + div[data-testid="stElementContainer"] div.stButton > button div,
    div[data-testid="stElementContainer"]:has(.chat-card-marker) + div[data-testid="stElementContainer"] div.stButton > button span {
        text-align: left !important;
        justify-content: flex-start !important;
        width: 100% !important;
        white-space: normal !important;
        word-break: break-word !important;
    }

    /* Bold Title inside Card */
    div[data-testid="stElementContainer"]:has(.chat-card-marker) + div[data-testid="stElementContainer"] div.stButton > button strong {
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        color: #111827 !important;
        display: block !important;
        margin-bottom: 4px !important;
    }
    </style>
    """, unsafe_allow_html=True)


def render_chats_list():
    _inject_chats_list_css()

    st.markdown("<h2>Chats</h2>", unsafe_allow_html=True)
    st.markdown("<p class='muted'>All your past conversations with Archi.</p>", unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    st.text_input("Search chats", key="chats_list_search", label_visibility="collapsed", placeholder="🔍 Search your chats...")
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    query = st.session_state.get("chats_list_search", "").strip().lower()
    chats = st.session_state.get("chats", {})

    if not chats:
        st.info("No chats yet.")
        return

    for chat_id, chat in chats.items():
        if query and query not in chat["title"].lower():
            continue

        # Extract latest message text for subtext preview
        last_msg = _extract_last_message(chat)
        preview = (last_msg[:100] + "...") if len(last_msg) > 100 else last_msg

        # Marker tag to scope CSS specifically to chat card buttons
        st.markdown('<div class="chat-card-marker"></div>', unsafe_allow_html=True)

        card_label = f"**{chat['title']}**\n\n{preview}"

        if st.button(card_label, key=f"chat_card_{chat_id}", use_container_width=True):
            st.session_state.active_chat_id = chat_id
            go("chat")