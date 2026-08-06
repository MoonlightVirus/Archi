"""
entity_extractor.py
--------------------
Finds which course (if any) a message is referring to.

Three passes, cheapest/most-certain first:
  1. Exact course code mention ("CBALGCM", "cbalgcm") -- word-boundary match
     against the real code list, longest codes checked first so e.g. "CBEMC1"
     isn't matched by a hypothetical shorter code that happens to be a prefix.
  2. Exact course name substring ("algorithms and complexity").
  3. Fuzzy match against course names, for typos/partial phrasing
     ("algorthms and complexity", "algorithms class").

Returns the course code (str) or None. None means "no course mentioned" --
callers should NOT guess in that case, since a wrong guess is worse than
asking a clarifying question.
"""
import difflib
import re


def extract_course(text: str, course_index: dict) -> str | None:
    if not text or not text.strip():
        return None

    text_low = text.lower()

    # Pass 1: exact code, longest first
    for code in sorted(course_index, key=len, reverse=True):
        if re.search(rf"\b{re.escape(code.lower())}\b", text_low):
            return code

    # Pass 2: exact course name substring
    for code, info in course_index.items():
        name_low = info["course_name"].lower()
        if name_low and name_low in text_low:
            return code

    # Pass 3: fuzzy match against course names (handles typos / loose phrasing)
    names_to_code = {info["course_name"]: code for code, info in course_index.items()}
    close = difflib.get_close_matches(text, list(names_to_code), n=1, cutoff=0.6)
    if close:
        return names_to_code[close[0]]

    return None
