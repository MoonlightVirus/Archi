"""Exact, explicit cross-dataset course resolution; never silently fuzzy-select."""
import re
from difflib import get_close_matches
from logic.academic.curriculum_engine import CurriculumEngine
from logic.course.course_lookup import COURSE_INDEX

CURRICULUM = CurriculumEngine()
ALIASES = {'CCPROG1': 'CBPROG1', 'CCPROG2': 'CBPROG2', 'CC/CBPROG1': 'CBPROG1', 'CC/CBPROG2': 'CBPROG2'}

def canonical(code):
    return ALIASES.get(code.upper(), code.upper())

def survey_key(code):
    return next((k for k in COURSE_INDEX if canonical(k) == code), None)

def _course_entries():
    entries = [(k, canonical(k)) for k in set(CURRICULUM.curriculum) | set(COURSE_INDEX) | set(ALIASES)]
    entries += [(value['name'], key) for key, value in CURRICULUM.curriculum.items()]
    entries += [(value['course_name'], canonical(key)) for key, value in COURSE_INDEX.items()]
    return sorted(entries, key=lambda entry: -len(entry[0]))

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
        names = {v['name'].lower(): k for k,v in CURRICULUM.curriculum.items()}
        suggestions = [names[n] for n in get_close_matches(text.lower(), list(names), n=3, cutoff=0.8)]
    return list(dict.fromkeys(suggestions))
