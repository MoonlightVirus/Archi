
# ARCHI

A modular Streamlit application for **ARCHI (Intelligent Academic Guide)**, an NLP-driven academic assistant for DLSU students. It features a white main canvas, a custom gradient dark-green sidebar, bright mint accents, pill-shaped controls, and bold typography.

The assistant understands academic questions via an intent-based NLP pipeline (handbook rules, GPA, flowchart/curriculum eligibility, course difficulty/workload/sentiment) and can compose mock consultation-request emails to professors through a built-in booking flow.

---

## How to Launch

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   Dependencies: `streamlit` and `nltk`.

2. **Run the Streamlit app**:
   ```bash
   streamlit run app.py
   ```

3. **Access the Application**:
   Open the local URL Streamlit displays in your terminal (usually `http://localhost:8501`). You will land on the Login screen first — enter any demo credentials or switch to Register to create a demo profile.

> `pipeline/preprocessor.py` runs completely offline using deterministic regex normalization and `COURSE_ALIAS_MAP` — no runtime NLTK corpus downloads are required.

---

##  Project Structure

```plaintext
ARCHI/
├── app.py                      # Application entry point: page config, session init, CSS injection, router
├── styles.py                   # Design tokens + global CSS overrides (fonts, buttons, modals, calendar grid)
├── state.py                    # Session state, demo data, chat bridge, and calendar/advisor UI helpers
├── chatbot_engine.py           # Thin facade over NLPPipeline
│
├── components/                 # Reusable UI elements & pop-up dialogs
│   ├── sidebar.py              # Gradient dark-green sidebar: branding, navigation, recent chats, profile row
│   ├── settings_modal.py       # Account settings dialog (st.dialog) — display name & notification toggles
│   ├── consultation_modal.py   # Consultation Details dialog (st.dialog) — topic, notes, GPA context
│   └── email_mockup.py         # Gmail-style draft email: preview/edit/send consultation requests
│
├── views/                      # Independent page views (routed via st.session_state)
│   ├── login.py                # Student authentication view
│   ├── register.py             # Student registration & onboarding view
│   ├── dashboard.py            # Main welcome screen with primary call-to-action buttons
│   ├── chat.py                 # Chat interface: sticky header, message bubbles, attachments, fixed input bar
│   ├── chats_list.py           # Full conversation history list with search filter & preview cards
│   ├── book_consultation.py    # Advising scheduler: monthly calendar, advisor cards, email draft tab
│   └── sus_form.py             # Standalone 10-question System Usability Scale survey (not yet wired in)
│
├── pipeline/                   # Per-chat, behavior-driven NLP pipeline
│   ├── context.py              # PipelineContext and workflow/session helpers
│   ├── preprocessor.py         # Offline normalization and course aliases
│   ├── interpreter.py          # Unified intent, entity, and control extraction
│   ├── routing/
│   │   ├── router.py           # Support/control → workflow lock → domain dispatch
│   │   └── support.py          # Crisis and academic-distress responses
│   ├── logic/
│   │   ├── retrieval.py        # Survey replies, handbook, prerequisites, eligibility
│   │   ├── booking.py          # Validation and multi-turn consultation drafts
│   │   ├── fallback.py         # Deterministic greeting and NLTK regex fallback
│   │   └── data/               # Course index, survey data, curriculum, aliases, academic JSON, handbook CSV
│   └── __init__.py             # NLPPipeline public API
│
├── tests/                      # Pipeline and Streamlit workflow regressions
│
├── static/                     # Glacial Indifference font files (referenced by styles.py)
└── requirements.txt            # streamlit, nltk
```

---

##  Module Breakdown

### Core Architecture
* **`app.py`**: Initializes session state, injects global styling, renders the logo, hides the sidebar on authentication pages, and routes views via `PAGE_MAP` (`dashboard`, `chat`, `chats_list`, `book_consultation`).
* **`styles.py`**: Color tokens (`DARK_GREEN`, `ACCENT`, `SIDEBAR_TOP`, etc.), `@font-face` rules for Glacial Indifference, button overrides, modal/dialog formatting, and calendar grid styling.
* **`state.py`**: Stores the demo student profile, calendar/advisor UI helpers, navigation, and a thin chat engine bridge. Booking parsers are re-exported for existing UI consumers.
* **`chatbot_engine.py`**: Exposes `get_response(user_input, session_state=None)` over `NLPPipeline.process_turn()`. Supply a separate mutable dictionary per chat for multi-turn interactions; omitting it creates an isolated one-turn context.
* **`pipeline/`**: Normalizes text without NLTK downloads, extracts intents/entities, then routes support and cancellation before workflow locks and domain handlers. Eligibility collects the target, passed courses, and term. Booking collects advisor, date, time, modality, and place, then emits `completed_booking` for the UI to open an editable draft. No email is sent by the pipeline. `booking_service`, when supplied to `NLPPipeline`, is a callable accepting the finalized draft.
* **`views/chat.py`**: Keeps pipeline state in `current_chat["session_state"]`, consumes completed drafts once, and opens the consultation email editor. Chat-owned draft cancellation leaves other chats' drafts and advisor lists intact.

Run regression tests with `python -m unittest discover -s tests -v`. Dates in consultation text use Asia/Manila time.

### Components (`components/`)
* **`sidebar.py`**: Dark-green gradient sidebar with active-nav highlights, scrollable recent-chat list, and the student profile/logout footer.
* **`settings_modal.py`**: Native `st.dialog` to update the display name and toggle email/deadline reminders.
* **`consultation_modal.py`**: Popup that captures topic/notes and builds the consultation email draft (jumps straight to the Email Draft tab).
* **`email_mockup.py`**: Gmail-style consultation-request draft with preview/edit/send modes. "Sending" only appends to `st.session_state.bookings` (mockup).

### Application Views (`views/`)
* **`login.py` & `register.py`**: Demo authentication screens — any credentials sign you in.
* **`dashboard.py`**: Welcome screen with quick-action buttons for booking a consultation or starting a chat.
* **`chat.py`**: Conversation view with sticky header + settings popover, user/assistant bubbles, attachment badges, a delayed-reply simulation, and a fixed bottom input form (text + file attach).
* **`chats_list.py`**: Full history list with search filtering and message-preview cards.
* **`book_consultation.py`**: Two tabs — **Schedule** (interactive monthly calendar with per-day booking chips, advisor cards with select/edit/add, meeting modality/venue pickers) and **Email Draft** (compose/send the consultation request).
* **`sus_form.py`**: A standalone System Usability Scale (SUS) survey with the 10 standard questions, auto-scoring, and grade interpretation. Not currently wired into the app.

---

##  How the Chat Responds

ARCHI answers across several domains:

| Topic | Source |
| --- | --- |
| Course difficulty / workload / tips / sentiment | Student survey data (`pipeline/logic/data/course_scores.json`, `course_sentiments.json`) |
| Handbook rules (grading, honors, graduation, audits, …) | `pipeline/logic/data/HandbookRules.csv` via `intent_to_rule_map.json` |
| Curriculum eligibility & prerequisites | `pipeline/logic/data/curriculum_data.json` via `CurriculumEngine` (multi-turn flow) |
| Consultation booking / rescheduling / cancellation | Multi-turn workflow in `pipeline/logic/booking.py` |
| Greetings, reassurance, small talk | NLTK Chat fallback pairs in `pipeline/logic/data/fallback_regex_pairs.json` |

---

##  Next Steps - Backend

* **Data Persistence**: Everything lives in `st.session_state`. Connect student profiles, chat history, advisor lists, and bookings to a database (e.g., PostgreSQL, Supabase, Firebase).
* **Email Delivery**: `components/email_mockup.py` only simulates sending. Wire the draft payload to a real email service (SMTP, SendGrid, Gmail API).
* **Authentication**: Replace the demo login/register logic with your institution's SSO or identity provider.
* **Live LLM / Real NLU**: `chatbot_engine.py` is rule- and data-driven. Swap in a language model or a real NLU service for broader understanding while keeping the intents above.
* **Connect the SUS survey**: Register `views/sus_form.py` in `app.py`'s `PAGE_MAP` and the sidebar when you're ready to collect usability data.
