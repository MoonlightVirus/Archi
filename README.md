
# ARCHI

A modular Streamlit application for **ARCHI (Intelligent Academic Guide)**, an NLP-driven academic assistant for DLSU students. It features a white main canvas, a custom gradient dark-green sidebar, bright mint accents, pill-shaped controls, and bold typography.

The assistant understands academic questions via an intent-based NLP pipeline (handbook rules, GPA, flowchart/curriculum eligibility, course difficulty/workload/sentiment) and can compose mock consultation-request emails to professors through a built-in booking flow.

---

## How to Launch

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   Dependencies: `streamlit`, `nltk`, and `tzdata`.

2. **Run the Streamlit app**:
   ```bash
   streamlit run app.py
   ```

3. **Access the Application**:
   Open the local URL Streamlit displays in your terminal (usually `http://localhost:8501`). You will land on the Login screen first — enter any demo credentials or switch to Register to create a demo profile.

> Shared preprocessing uses resource-independent tokenization; no NLTK corpus downloads are required.

---

##  Project Structure

```plaintext
ARCHI/
├── app.py                      # Application entry point: page config, session init, CSS injection, router
├── styles.py                   # Design tokens + global CSS overrides (fonts, buttons, modals, calendar grid)
├── state.py                    # Session state, demo data, chat engine bridge, and consultation booking logic
├── chatbot_engine.py           # NLP response engine: course queries, handbook rules, eligibility flow, NLTK fallback
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
|-- logic/                      # Four specialized logic groups
|   |-- course/                 # Survey intents, lookup, entity extraction, handler and responses
|   |-- academic/               # Handbook, curriculum, eligibility, classifiers and policy data
|   |-- booking/                # Scheduling parser, action service and handler
|   `-- fallback/               # NLTK conversational handler and regex pairs
|
|-- routing/                    # Shared interpretation, course resolution, context and pure router
|   |-- preprocessor.py         # Shared tokens, negation, numbers and character spans
|   |-- support.py              # Shared distress detection and support responses
|   `-- handlers/               # Group dispatch and common handler context helpers
|
|-- dialogue/
|   `-- turn_renderer.py        # Shared structured-result rendering
|
|-- tests/                      # Router acceptance tests and Streamlit integration check
|
├── data/                       # Data-driven bot answers
│   ├── course_scores.json      # Survey difficulty/workload ratings + tips per course
│   ├── course_sentiments.json  # Survey sentiment/comments per course
│   └── curriculum_data.json    # Courses, prerequisites, corequisites, offered terms
│
├── static/                     # Glacial Indifference font files (referenced by styles.py)
└── requirements.txt            # streamlit, nltk
```

---

##  Module Breakdown

### Core Architecture
* **`app.py`**: Initializes session state, injects global styling, renders the logo, hides the sidebar on authentication pages, and routes views via `PAGE_MAP` (`dashboard`, `chat`, `chats_list`, `book_consultation`).
* **`styles.py`**: Color tokens (`DARK_GREEN`, `ACCENT`, `SIDEBAR_TOP`, etc.), `@font-face` rules for Glacial Indifference, button overrides, modal/dialog formatting, and calendar grid styling.
* **`state.py`**: Stores demo/session data, advisor management and navigation helpers. Scheduling parsing and booking operations live in `logic/booking/`.
* **`chatbot_engine.py`**: Orchestrates interpretation, routing, the selected group handler, result rendering and per-chat result caching. Distress and flow controls are shared routing concerns.
* **`logic/course/`**: Course difficulty, workload, tips, sentiment and overviews, including survey response templates.
* **`logic/academic/`**: Handbook retrieval, prerequisite checks, eligibility, and guidance on unavailable GPA/flowchart features.
* **`logic/booking/`**: Scheduling extraction, draft preparation and identified cancellation.
* **`logic/fallback/`**: Greetings, thanks and unsupported-request guidance.

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
| Course difficulty / workload / tips / sentiment | Student survey data (`data/course_scores.json`, `data/course_sentiments.json`) |
| Handbook rules (grading, honors, graduation, audits, …) | `logic/academic/HandbookRules.csv` via `intent_to_rule_map.json` |
| Curriculum eligibility & prerequisites | `data/curriculum_data.json` via `CurriculumEngine` (multi-turn flow) |
| Consultation booking / rescheduling / cancellation | Injected service in `logic/booking/service.py` |
| Greetings, reassurance, small talk | NLTK Chat fallback pairs in `logic/fallback/fallback_regex_pairs.json` |

---

##  Next Steps - Backend

* **Data Persistence**: Everything lives in `st.session_state`. Connect student profiles, chat history, advisor lists, and bookings to a database (e.g., PostgreSQL, Supabase, Firebase).
* **Email Delivery**: `components/email_mockup.py` only simulates sending. Wire the draft payload to a real email service (SMTP, SendGrid, Gmail API).
* **Authentication**: Replace the demo login/register logic with your institution's SSO or identity provider.
* **Live LLM / Real NLU**: `chatbot_engine.py` is rule- and data-driven. Swap in a language model or a real NLU service for broader understanding while keeping the intents above.
* **Connect the SUS survey**: Register `views/sus_form.py` in `app.py`'s `PAGE_MAP` and the sidebar when you're ready to collect usability data.

## Central message router

All interactive messages enter `chatbot_engine.process_chat_message`. Each chat owns
its context, pending message ID and processed-result cache. The cache prevents
ordinary Streamlit reruns from executing an action or appending a reply twice;
it is session memory, not durable crash recovery.

`routing.interpreter.interpret` and `routing.router.route` are read-only. They
produce evidence and explicit rule IDs; specificity is an ordering rule, not a
probability. Domain handlers return a structured status and reply data. Only the
injected `logic.booking.service.BookingService` changes consultation records. Routine
logs contain route, intent, rule, status and context transition, not message text.

Eligibility collects passed courses, other previously taken courses, and the
enrollment term separately. Soft prerequisites retain the existing engine rule:
they must previously have been taken. Confirm any future academic policy change
separately. GPA calculations, generated flowcharts, live availability, real email
delivery and calendar updates remain unavailable. Consultation actions prepare
mock email drafts; cancellation never removes an advisor.

Course aliases are explicit in `routing/courses.py`. Unknown or fuzzy matches
require confirmation. Tokenization preserves numbers, negation and character
positions and does not download NLTK resources. NLTK Chat is limited to greetings
and thanks, with a resource-independent reply if NLTK is unavailable.

Run checks from the repository root:

```powershell
python -m unittest discover -s tests -v
```

`tests/test_router.py` is the deterministic route/state/effect acceptance set.
`tests/test_streamlit.py` runs the actual app with Streamlit AppTest and checks chat
switching, pending-flow isolation, draft ownership, booking-page navigation,
cancellation, return to chat and rerun behavior. The pre-migration baseline had
first-match greeting/survey routing, process-global eligibility context, and
booking mutations before the engine. The acceptance set records the corrected
outcomes; no shadow execution of old booking actions is performed.
