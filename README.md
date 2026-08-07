
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

> On first run, `pipeline/preprocessor.py` automatically downloads the NLTK data it needs (`punkt_tab`, `stopwords`, `wordnet`, `averaged_perceptron_tagger_eng`).

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
├── nlu/                        # Lightweight course-NLP: difficulty / workload / tips / sentiment
│   ├── intent_classifier.py    # Narrow intent patterns for course queries
│   ├── course_lookup.py        # Merged course-scores + sentiment index, built once at import
│   └── entity_extractor.py     # Resolves course codes/names (variants, typos, prefix-stripping)
│
├── dialogue/                   # Course-response generation
│   ├── response_generator.py   # Formats data into final replies (per intent)
│   └── response_templates.py   # Plain-string templates for course replies
│
├── pipeline/                   # Core NLP preprocessing + intent classification
│   ├── preprocessor.py         # Tokenize → POS tag → lemmatize → clean (NLTK)
│   ├── featureExtraction.py    # Dictionary + NNP entity extraction, parameter binding
│   ├── intent_classifier.py    # Maps extracted entities to intents (handbook, curriculum, GPA, …)
│   ├── curriculum_engine.py    # Prerequisite/eligibility checking + recommendations
│   ├── academic_entities.json  # Entity phrase dictionary
│   ├── binding_rules.json      # Action→target binding & POS constraints
│   └── __init__.py             # Re-exports the pipeline entry points
│
├── responses/                  # NLG data
│   ├── intent_responses.json   # Intent → response templates
│   ├── fallback_regex_pairs.json  # NLTK Chat regex fallback pairs
│   └── intent_to_rule_map.json # Entity category → handbook rule ID
│
├── references/
│   ├── csv_parser.py           # Parses HandbookRules.csv into a hierarchical rule dict
│   └── HandbookRules.csv       # DLSU student handbook rules (Section 10–12)
│
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
* **`state.py`**: Stores the demo student profile, curriculum structures, initial chat seeding, and consultation booking logic: natural-language date/time/modality/place parsing, professor extraction, a session advisor registry (add/edit), booking intent & cancel detection, and `go()`/`new_chat()` navigation helpers.
* **`chatbot_engine.py`**: The response engine. Order of handling:
  1. **Course intent queries** (`nlu/`) — difficulty, workload, tips, sentiment for a named course.
  2. **NLP pipeline** — preprocess → feature extraction → multi-turn curriculum/eligibility flow → `IntentClassifier` (handbook rules, eligibility checks, GPA, flowchart, consultations) → `INTENT_RESPONSES`.
  3. **Course overview fallback** — bare course-code mentions.
  4. **NLTK Chat** — broad regex fallbacks (greetings, emotions, thanks).
  5. Generic `FALLBACK_RESPONSE`.

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
| Handbook rules (grading, honors, graduation, audits, …) | `references/HandbookRules.csv` via `intent_to_rule_map.json` |
| Curriculum eligibility & prerequisites | `data/curriculum_data.json` via `CurriculumEngine` (multi-turn flow) |
| Consultation booking / rescheduling / cancellation | Session-state booking engine in `state.py` |
| Greetings, reassurance, small talk | NLTK Chat fallback pairs in `responses/fallback_regex_pairs.json` |

---

##  Next Steps - Backend

* **Data Persistence**: Everything lives in `st.session_state`. Connect student profiles, chat history, advisor lists, and bookings to a database (e.g., PostgreSQL, Supabase, Firebase).
* **Email Delivery**: `components/email_mockup.py` only simulates sending. Wire the draft payload to a real email service (SMTP, SendGrid, Gmail API).
* **Authentication**: Replace the demo login/register logic with your institution's SSO or identity provider.
* **Live LLM / Real NLU**: `chatbot_engine.py` is rule- and data-driven. Swap in a language model or a real NLU service for broader understanding while keeping the intents above.
* **Connect the SUS survey**: Register `views/sus_form.py` in `app.py`'s `PAGE_MAP` and the sidebar when you're ready to collect usability data.
