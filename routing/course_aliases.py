"""Build course aliases from curriculum and survey data."""
import re


def normalize_code(code):
    return re.sub(r'[^A-Z0-9]', '', code.upper())


def _normalize_name(name):
    return normalize_code(name.replace('&', ' and '))


def _code_variants(code, prefixes):
    parts = code.upper().split('/')
    variants = {code.upper(), parts[-1]}
    for part in parts[:-1]:
        # Compact alternatives such as CC/CBPROG1 share the suffix PROG1.
        if part.isalpha() and len(part) < len(parts[-1]):
            variants.add(part + parts[-1][len(part):])
        else:
            variants.add(part)
    for variant in tuple(variants):
        if '/' in variant:
            continue
        for prefix, alternatives in prefixes.items():
            if variant.startswith(prefix):
                variants.update(other + variant[len(prefix):] for other in alternatives)
                variants.update(other + '/' + variant for other in alternatives if other != prefix)
    return variants


def build_aliases(curriculum, course_index):
    codes = set(curriculum) | set(course_index)
    prefixes = {}
    for code in codes:
        parts = code.upper().split('/')
        for prefix in parts[:-1]:
            if prefix.isalpha() and len(prefix) < len(parts[-1]):
                alternatives = {prefix, parts[-1][:len(prefix)]}
                for alternative in alternatives:
                    prefixes.setdefault(alternative, set()).update(alternatives)

    variants = {code: _code_variants(code, prefixes) for code in codes}
    curriculum_codes = {}
    curriculum_names = {}
    for code, course in curriculum.items():
        for variant in variants[code]:
            curriculum_codes.setdefault(normalize_code(variant), set()).add(code)
        curriculum_names.setdefault(_normalize_name(course['name']), set()).add(code)

    targets = {code: code for code in curriculum}
    for code, course in course_index.items():
        if code in targets:
            continue
        matches = set()
        for variant in variants[code]:
            matches.update(curriculum_codes.get(normalize_code(variant), ()))
        if not matches:
            matches = curriculum_names.get(_normalize_name(course['course_name']), set())
        targets[code] = next(iter(matches)) if len(matches) == 1 else code

    candidates = {}
    for code, target in targets.items():
        for variant in variants[code]:
            candidates.setdefault(variant, set()).add(target)
    aliases = {variant: next(iter(matches)) for variant, matches in candidates.items() if len(matches) == 1}
    # An explicitly stored code always takes priority over inferred variants.
    aliases.update(targets)
    return aliases


def build_normalized_aliases(aliases):
    candidates = {}
    for alias, code in aliases.items():
        candidates.setdefault(normalize_code(alias), set()).add(code)
    return {alias: next(iter(matches)) for alias, matches in candidates.items() if len(matches) == 1}
