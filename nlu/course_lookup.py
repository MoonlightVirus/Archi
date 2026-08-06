"""
course_lookup.py
-----------------
Loads course_scores.json + course_sentiment.json once at import time and
builds a merged index keyed by Course Code, plus a code->code passthrough
and course_name->code map used by entity_extractor.py.
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"


def _load_json(name: str) -> dict:
    path = DATA_DIR / name
    with open(path, "r") as f:
        return json.load(f)


def build_course_index() -> dict:
    """
    Returns {course_code: {..scores.., ..sentiment..}} -- one merged record
    per course so the response generator only needs a single lookup.
    """
    scores = _load_json("course_scores.json")
    sentiment = _load_json("course_sentiment.json")

    index = {}
    for code, score_info in scores.items():
        merged = dict(score_info)
        merged.update(sentiment.get(code, {}))
        index[code] = merged
    return index


# Built once at import time -- chatbot_engine.py imports COURSE_INDEX directly,
# so this never re-reads disk per message.
COURSE_INDEX = build_course_index()

# code -> full name lookup, used by the response templates
CODE_TO_NAME = {code: info["course_name"] for code, info in COURSE_INDEX.items()}
