"""Exact, explicit cross-dataset course resolution; never silently fuzzy-select."""
import re
from difflib import get_close_matches
from logic.academic.curriculum_engine import CurriculumEngine
from logic.course.course_lookup import COURSE_INDEX
from .course_aliases import build_aliases, build_normalized_aliases, normalize_code

CURRICULUM = CurriculumEngine()
ALIASES = build_aliases(CURRICULUM.curriculum, COURSE_INDEX)
NORMALIZED_ALIASES = build_normalized_aliases(ALIASES)

def canonical(code):
    code = code.upper()
    return ALIASES.get(code, NORMALIZED_ALIASES.get(normalize_code(code), code))

def survey_key(code):
    code = canonical(code)
    return next((k for k in COURSE_INDEX if canonical(k) == code), None)

def _course_entries():
    entries = dict(ALIASES)
    for alias, code in NORMALIZED_ALIASES.items():
        entries.setdefault(alias, code)
    names = {}
    for key, value in CURRICULUM.curriculum.items():
        names.setdefault(value['name'].casefold(), set()).add(canonical(key))
    for key, value in COURSE_INDEX.items():
        names.setdefault(value['course_name'].casefold(), set()).add(canonical(key))
    for name, codes in names.items():
        if len(codes) == 1:
            entries.setdefault(name, next(iter(codes)))
    return sorted(entries.items(), key=lambda entry: (-len(entry[0]), entry[0]))

def _overlaps(match, mentions):
    return any(match.start() < mention['end'] and match.end() > mention['start'] for mention in mentions)

def resolve_courses(text):
    mentions = []
    for phrase, code in _course_entries():
        pattern = r'(?<!\w)' + re.escape(phrase) + r'(?!\w)'
        for match in re.finditer(pattern, text, re.I):
            if _overlaps(match, mentions):
                continue
            mentions.append({
                'code': code,
                'survey_key': survey_key(code),
                'start': match.start(),
                'end': match.end(),
            })
    return sorted(mentions, key=lambda m: m['start'])


def suggest_courses(text):
    codes = list(CURRICULUM.curriculum)
    suggestions = []
    for token in re.findall(r"\b[A-Za-z]{2,}[A-Za-z0-9-]*\b", text):
        if token.upper().startswith(('CB', 'CC', 'LBY', 'THS')):
            suggestions.extend(get_close_matches(token.upper(), codes, n=3, cutoff=0.72))
    if not suggestions:
        names = {}
        for code, course in CURRICULUM.curriculum.items():
            names.setdefault(course['name'].lower(), []).append(code)
        suggestions = [code for name in get_close_matches(text.lower(), list(names), n=3, cutoff=0.8)
                       for code in names[name]]
    return list(dict.fromkeys(suggestions))
