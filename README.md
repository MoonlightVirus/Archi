
# ARCHI 

A modular Streamlit frontend for **ARCHI (Intelligent Academic Guide)**,  featuring a white main canvas, a custom gradient dark-green sidebar, bright mint accents, pill-shaped controls, and bold typography.

---

## How to Launch

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Streamlit app**:
   ```bash
   streamlit run app.py
   ```

3. **Access the Application**:
   Open the local URL Streamlit displays in your terminal (usually `http://localhost:8501`). You will land on the Login screen first — enter any demo credentials or switch to Register to create a demo profile.

---

##  Project Structure

```plaintext
ARCHI/
├── app.py                      # Application entry point: page configuration, session init, CSS injection, router
├── styles.py                   # Design tokens + global CSS overrides (fonts, buttons, modals, calendar grid)
├── state.py                    # Session state defaults, initial seeding, and sample datasets (profile, advisors, chats)
│
├── components/                 # Reusable UI elements & pop-up dialogs
│   ├── sidebar.py              # Gradient dark-green sidebar: branding header, navigation, recent chats list, profile row
│   ├── settings_modal.py       # Account settings dialog (st.dialog) — display name & notification toggles
│   └── consultation_modal.py   # Consultation Details dialog (st.dialog) — concern topic, notes, student GPA context
│
└── views/                      # Independent page views (routed via st.session_state)
    ├── login.py                # Student authentication view
    ├── register.py             # Student registration & onboarding view
    ├── dashboard.py            # Main welcome screen with primary call-to-action buttons
    ├── chat.py                 # Chat interface: sticky header, message bubbles, attachment badge, fixed input bar
    ├── chats_list.py           # Full conversation history list with search filter & preview cards
    └── book_consultation.py    # Academic advising scheduler: monthly calendar, time slots, advisor status list
```

---

##  Module Breakdown

### Core Architecture
* **`app.py`**: Initializes session state, injects global styling, handles dark-green logo rendering, hides the sidebar on authentication pages, and routes views using `PAGE_MAP`.
* **`styles.py`**: Contains color tokens (`DARK_GREEN`, `ACCENT`, `SIDEBAR_TOP`, etc.), custom `@font-face` rules for Glacial Indifference, button overrides, and modal formatting rules, and all external CSS elements.
* **`state.py`**: Stores default student profile data, curriculum structures, initial chat seeding, page navigation triggers (`go()`), new chat creation (`new_chat()`), and keyword-matching responses (`bot_reply()`).

### Components (`components/`)
* **`sidebar.py`**: Renders the dark-green gradient sidebar, active navigation row highlights, scrollable recent chat list with search matching, and the student profile/logout footer.
* **`settings_modal.py`**: A native Streamlit dialog (`st.dialog`) allowing users to update their display name and toggle email/deadline reminders.
* **`consultation_modal.py`**: A popup dialog triggered when booking an advising session, displaying advisor info, topic dropdowns, note fields, and GPA recommendations.

### Application Views (`views/`)
* **`login.py` & `register.py`**: Student authentication screens providing structured form inputs and navigation toggles.
* **`dashboard.py`**: The landing welcome screen providing quick-action links to book a consultation or start a chat.
* **`chat.py`**: The primary conversation view featuring a sticky header with chat settings popover, assistant/user message bubbles, attachment badges, and a fixed bottom input form.
* **`chats_list.py`**: Displays all past student interactions with search filtering and message preview snippets.
* **`book_consultation.py`**: Features an interactive monthly calendar matrix, time slot selection, advisor availability status, and booking modal triggers.

---

##  Next Steps - Backend

* **AI Guidance Engine**: Replace `bot_reply()` in `state.py` with an API call to your language model or academic guidance service.
* **Document Parser**: Connect the file uploader handler in `views/chat.py` to your flowchart analysis pipeline.
* **Data Persistence**: `state.py` relies on in-memory `st.session_state`. Connect student profiles, chat history, and advising bookings to a database (e.g., PostgreSQL, Supabase, Firebase).
* **Authentication**: Replace the demo submit logic in `views/login.py` and `views/register.py` with your institution's SSO or identity provider.
