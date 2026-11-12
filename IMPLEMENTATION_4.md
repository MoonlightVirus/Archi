# Implementation 4: consolidated pipeline with context-aware routing

The application keeps one processing entry point under `pipeline/`. Interpretation
collects intent candidates; routing decides whether the message is a control,
clarification, workflow answer, or new request before invoking domain logic.

## Turn processing

```text
Chat message + stable message ID + per-chat session
  -> NLPPipeline.process_result
  -> normalize text and course aliases
  -> extract entities, control flags, and intent candidates
  -> router
       support / cancellation / negation
       clarification selection / resume / missing-course selection
       valid workflow slot answer
       competing intents -> clarification
       explicit request -> selected domain
       remaining workflow follow-up / fallback
  -> course or academic retrieval, booking, or fallback
  -> TurnResult(reply, status, diagnostics, duplicate)
```

`process_turn()` and `chatbot_engine.get_response()` retain their string-returning
interfaces. Pass a mutable dictionary for each chat. Calls without a dictionary
are isolated single-turn requests.

```python
from pipeline import NLPPipeline

pipeline = NLPPipeline()
session = {}
result = pipeline.process_result(
    "Am I eligible for CBOPESY?", session, message_id="submission-1"
)
print(result.reply)
print(result.status, result.diagnostics["rule_id"])
```

## Conversation behavior

- A side question such as "Actually, what are its prerequisites?" retains the
  previous course and leaves the unfinished eligibility or booking slots intact.
- Independent intents such as difficulty and workload produce a numbered
  clarification. Reply with the number or intent label. Candidate entities retain
  their course association when the requests mention different courses.
- Missing, multiple, or misspelled course codes trigger a course-selection prompt.
  Selecting a course continues the original intent rather than giving an overview.
- Switching between booking and eligibility saves the other workflow. `resume`
  restores the most recently suspended workflow and repeats its pending prompt.
  A new explicit request for the same workflow replaces its old saved version.
- Eligibility collects passed courses, other previously taken courses (including
  failed courses), and enrollment term separately. Passed courses also count as
  taken; only passed courses satisfy hard prerequisites. Invalid and negated
  course lists do not advance the workflow.
- Support and generic cancellation clear unfinished workflows and clarifications.
  Consultation-policy questions and negated booking commands do not cancel drafts.
- Booking completion still opens an editable email draft. The pipeline itself
  does not send email.

## State, diagnostics, and retries

Each chat owns its workflow state and processed-message cache. The UI generates a
new ID for each submission and stores `reply_to` on assistant messages. Pending
messages belong to their chat, so navigating to another chat cannot consume them.
An attachment-only submission receives an attachment response, not a replay of
the previous text prompt.

Reusing an ID with the same text returns the cached result with `duplicate=True`
without calling a domain handler or re-emitting a consumed booking event. Reusing
an ID with different text raises `ValueError`. Identical text submitted with a new
ID is a new request. The cache lasts only for the in-memory chat session.

Diagnostics include the route ID, group, selected intent, candidates, status, and
workflow/slot transitions. They are logged and saved with assistant messages, not
shown as part of normal chat replies. Domain work uses a copy of session state;
handler errors retain the prior workflow state and return an `error` result.
An error result is cached for its message ID too; an explicit retry is a new
submission with a new ID.

An injected booking service remains an optional callable accepting the draft.
The in-memory message cache prevents repeat calls for replayed submissions; it
does not guarantee durable exactly-once behavior across crashes or external
service failures. Such services must provide their own durable idempotency.

## Verification

Run the regression suite with the project's Python environment:

```text
python -m unittest discover -s tests -v
```

The suite covers aliases, retrieval, clarification, course selection, safe policy
questions, negation, workflow switching, eligibility, support/cancellation,
per-chat isolation, error rollback, and duplicate booking prevention. The live
Streamlit chat was also exercised through eligibility, a side question, intent
clarification, a plain rerun, and editable consultation-draft creation.

The system remains rule-based. Legacy academic templates are not implementations
of personalized GPA calculations, flowchart updates, or external calendar actions.
