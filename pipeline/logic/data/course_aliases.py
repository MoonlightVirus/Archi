"""Read-only aliases and fuzzy course suggestions shared by normalization and retrieval."""
from difflib import get_close_matches
import re
from types import MappingProxyType
from typing import Mapping
from .courses import COURSE_INDEX, CURRICULUM


def normalize_alias(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _build_aliases() -> tuple[dict[str, str], dict[str, str]]:
    aliases: dict[str, str] = {}
    # Survey codes take precedence; curriculum code resolution stays separate.
    for code in [*COURSE_INDEX, *CURRICULUM.curriculum]:
        normalized = normalize_alias(code)
        canonical = aliases.get(code.lower(), code)
        variants = {code.lower(), normalized, *code.lower().split("/")}
        current = normalized
        while current.startswith(("cc", "cb")) and len(current) > 5:
            current = current[2:]
            variants.add(current)
        for variant in list(variants):
            variants.add(re.sub(r"(?<=[a-z])(?=\d)", " ", variant.replace("-", " ")))
        info = COURSE_INDEX.get(code, {})
        name = info.get("course_name") or CURRICULUM.get_course_name(code)
        if name:
            variants.add(name.lower())
        for variant in variants:
            aliases.setdefault(variant, canonical)
    return aliases, {normalize_alias(k): v for k, v in aliases.items()}


_aliases, _normalized = _build_aliases()
COURSE_ALIAS_MAP: Mapping[str, str] = MappingProxyType(_aliases)
NORMALIZED_ALIAS_MAP: Mapping[str, str] = MappingProxyType(_normalized)


def curriculum_code(code: str) -> str:
    """Resolve survey codes such as CC/CBPROG1 to curriculum codes."""
    if CURRICULUM.course_exists(code):
        return code.upper()
    for part in reversed(code.split("/")):
        if CURRICULUM.course_exists(part):
            return part.upper()
    return code.upper()


def suggest_courses(text: str, limit: int = 3) -> list[str]:
    """Suggest canonical course codes for near-miss code tokens in user text."""
    suggestions: list[str] = []
    tokens = re.findall(r"[a-zA-Z]{3,}[a-zA-Z0-9-]*", text.lower())
    stop = {
        "what", "which", "where", "when", "take", "pass", "passed", "course", "courses",
        "hard", "difficult", "difficulty", "workload", "tips", "advice", "prepare", "survive",
        "worth", "taking", "recommend", "recommended", "opinion", "thoughts", "reviews",
        "comments", "sentiment", "think", "feel", "about", "prerequisite", "prerequisites",
        "prereq", "prereqs", "corequisite", "corequisites", "eligible", "eligibility",
        "qualified", "allowed", "enroll", "offered", "offerings", "available", "term", "terms",
    }
    for token in tokens:
        norm = normalize_alias(token)
        if norm in stop or len(norm) < 4:
            continue
        # Prefix/substring matches on known normalized aliases first
        for alias_norm, canonical in NORMALIZED_ALIAS_MAP.items():
            if len(alias_norm) <= 10 and (alias_norm.startswith(norm) or norm.startswith(alias_norm)):
                if canonical not in suggestions:
                    suggestions.append(canonical)
        # Close Levenshtein matches on short code aliases
        short_keys = [k for k in NORMALIZED_ALIAS_MAP if 4 <= len(k) <= 10]
        for match in get_close_matches(norm, short_keys, n=limit, cutoff=0.78):
            canonical = NORMALIZED_ALIAS_MAP[match]
            if canonical not in suggestions:
                suggestions.append(canonical)
        if len(suggestions) >= limit:
            break
    return suggestions[:limit]

