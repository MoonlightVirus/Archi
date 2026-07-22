# ARCHI — Streamlit Frontend

A modular Streamlit frontend for **ARCHI (Intelligent Academic Guide)**, built from
the ARCHI Website Mockup Design: white main canvas, a solid dark-green sidebar,
a bright mint wordmark, pill-shaped light-gray controls, and bold rounded type.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL Streamlit prints (usually `http://localhost:8501`). You'll land
on the Login page first — any credentials work (it's a demo login), or use
Register to create a demo profile.

## Project structure

```
app.py                          entry point: page config, session init, CSS, auth gate, router
styles.py                       design tokens + inject_global_css()
state.py                        session-state defaults + sample data (profile, advisors, chats, curriculum)

components/
  sidebar.py                    the dark-green sidebar: logo, nav, chat search, recent chats, profile row
  settings_modal.py             Settings popup (st.dialog) — simple toggles + display name
  consultation_modal.py         "Consultation Details" popup (st.dialog) from the mockup

views/
  login.py                      Login page
  register.py                  Register page
  dashboard.py                  "Welcome, {name}!" page with the two big pill actions
  chat.py                       chat conversation view (bubbles, file attachment, chat input)
  chats_list.py                 full chat history list (à la Claude's chat history page)
  book_consultation.py          calendar + advisor picker + opens the Consultation Details modal
```

Each page lives in its own file under `views/`, and shared UI pieces (sidebar,
the two modals) live under `components/` — so you can hand any single page to
someone to edit without touching the rest of the app.

Note: the folder is named `views/`, not `pages/` — Streamlit auto-generates its
own multi-page navigation for anything in a `pages/` directory, which would
fight with the custom sidebar here. Routing is handled manually in `app.py`
via `st.session_state.page`.

## Where to wire up a real backend

- `state.py` holds all the sample data (`DEFAULT_PROFILE`, `ADVISORS`, `CURRICULUM`,
  the seeded chats) — swap these for real API/database calls.
- `bot_reply()` in `state.py` is a placeholder keyword-matcher for the chat —
  replace it with a call to your LLM/backend for real academic guidance.
- Chats, bookings, and the profile all live in `st.session_state` only, so they
  reset when the server restarts. Persist them to a database if needed.
- The file uploader in `views/chat.py` currently just acknowledges the upload —
  wire it to whatever service will actually parse a flowchart PDF.
- Login/Register don't check credentials against anything real yet — they just
  flip `st.session_state.logged_in`.
