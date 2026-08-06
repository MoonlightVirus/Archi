"""
intent_classifier.py
---------------------
Classifies what a user wants to know about a course. Checked in order --
first match wins, same convention as the existing nltk pairs in
chatbot_engine.py.

Kept intentionally narrow: these patterns should only fire on messages that
are clearly asking about course difficulty/workload/tips/sentiment, so they
don't accidentally intercept unrelated messages meant for Marthy/Renee/Louis
(e.g. Renee's GPA patterns, Marthy's flowchart/consultation patterns).
"""
import re

INTENT_PATTERNS = [
    ("difficulty", re.compile(r"\b(hard|difficult|difficulty|tough|rigorous)\b", re.I)),
    ("workload", re.compile(r"\b(workload|pacing|busy|time.?consuming|how much work)\b", re.I)),
    ("tips", re.compile(r"\b(tips?|advice|prepare|survive)\b", re.I)),
    ("sentiment", re.compile(r"\b(worth it|worth taking|recommend(?:ed)?|opinion|thoughts?|reviews?|comments?|like it|sentiment|think of|feel about|say about)\b", re.I))
]


def classify_intent(text: str) -> str | None:
    if not text:
        return None
    for intent, pattern in INTENT_PATTERNS:
        if pattern.search(text):
            return intent
    return None
