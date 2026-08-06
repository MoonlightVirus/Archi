"""
response_templates.py
----------------------
Plain string templates, filled by response_generator.py. Kept separate from
the generator so wording can be tweaked without touching the lookup/fallback
logic.
"""

DIFFICULTY = (
    "{name} ({code}) has an average difficulty of {diff}/5 ({diff_label}), "
    "based on {n} rating{n_plural}.{low_n_note}"
)

WORKLOAD = (
    "{name} ({code}) has an average workload rating of {work}/5 ({work_label}), "
    "based on {n} rating{n_plural}.{low_n_note}"
)

TIPS_WITH_DATA = "Here's what past students said about {name}:\n{sample_tips}"
TIPS_NO_DATA = "No written tips are available yet for {name} ({code})."

SENTIMENT_WITH_DATA = (
    "Overall sentiment on {name} is {sent_label} ({pct_pos}% of comments positive), "
    "based on {n_comments} comment{n_comments_plural}. Common themes: {themes}."
)
SENTIMENT_NO_DATA = "No comments are available yet to gauge sentiment on {name} ({code})."

OVERVIEW = (
    "{name} ({code}): difficulty {diff}/5 ({diff_label}), workload {work}/5 ({work_label}), "
    "sentiment {sent_label}.{low_n_note}\n{top_tip_line}"
)

NO_RATING_DATA = "No difficulty/workload ratings are available yet for {name} ({code})."

CLARIFY_WHICH_COURSE = (
    "Which course are you asking about? You can use its course code (e.g. CBALGCM) "
    "or its full name."
)

COURSE_NOT_FOUND = (
    "I couldn't find that course. Could you double-check the course code or name?"
)

LOW_N_NOTE_TEMPLATE = " (Note: this is based on a small number of responses, so take it with a grain of salt.)"
LOW_N_THRESHOLD = 3
