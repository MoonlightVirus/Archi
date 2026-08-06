"""
entity_extractor.py
--------------------
Finds which course (if any) a message is referring to.

"""
import difflib
import re

_PREFIXES = ("cc", "cb")

_MIN_STRIPPED_LEN = 3


def _normalize_code(text: str) -> str:
    """Strip to lowercase alphanumerics: 'CBEMC-1' -> 'cbemc1'."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _prefix_stripped_variants(normalized_code: str) -> set:
    """
    Repeatedly strips known prefixes off the front of a normalized code,
    collecting every intermediate result. 'cccbprog1' (from 'CC/CBPROG1')
    yields {'cbprog1', 'prog1'}; 'cbdsalg' (from 'CBDSALG') yields {'dsalg'}.
    """
    variants = set()
    current = normalized_code
    changed = True
    while changed:
        changed = False
        for prefix in _PREFIXES:
            if current.startswith(prefix) and len(current) - len(prefix) >= _MIN_STRIPPED_LEN:
                current = current[len(prefix):]
                variants.add(current)
                changed = True
                break  # restart the prefix scan on the newly-stripped string
    return variants


def _build_code_variants(course_index: dict) -> dict:
    """
    Maps every way a user might type a course code to the real code:
    the punctuation-normalized form, plus every prefix-stripped form
    (e.g. 'dsalg' -> 'CBDSALG', 'prog1' -> 'CC/CBPROG1').
    """
    variants = {}
    for code in course_index:
        stripped = _normalize_code(code)
        variants[stripped] = code
        for shorter in _prefix_stripped_variants(stripped):
            variants.setdefault(shorter, code)
    return variants


def _token_candidates(text: str) -> list:
    """
    Whitespace tokens with punctuation stripped, plus joins of adjacent
    tokens so a spaced code ('CBEMC 1', 'CC CBPROG1', 'ST MATH') still
    resolves. Joins only match when they exactly equal a real code variant,
    so they can't produce false positives.
    """
    tokens = text.lower().split()
    candidates = []
    for token in tokens:
        stripped = _normalize_code(token)
        if stripped:
            candidates.append(stripped)
    for left, right in zip(tokens, tokens[1:]):
        joined = _normalize_code(left) + _normalize_code(right)
        if joined:
            candidates.append(joined)
    return candidates


def extract_course(text: str, course_index: dict) -> str | None:
    if not text or not text.strip():
        return None

    text_low = text.lower()

    # Pass 1: exact code with canonical punctuation, longest first
    for code in sorted(course_index, key=len, reverse=True):
        if re.search(rf"\b{re.escape(code.lower())}\b", text_low):
            return code

    # Pass 2: normalized + prefix-stripped variants, longest candidate first
    variants = _build_code_variants(course_index)
    for candidate in sorted(_token_candidates(text), key=len, reverse=True):
        if candidate in variants:
            return variants[candidate]

    # Pass 3: exact course name substring
    for code, info in course_index.items():
        name_low = info["course_name"].lower()
        if name_low and name_low in text_low:
            return code

    # Pass 4: fuzzy match against course names (handles typos / loose phrasing)
    names_to_code = {info["course_name"]: code for code, info in course_index.items()}
    close = difflib.get_close_matches(text, list(names_to_code), n=1, cutoff=0.6)
    if close:
        return names_to_code[close[0]]

    return None