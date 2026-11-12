"""Course surveys, curriculum eligibility, and handbook retrieval."""
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
    "{name} ({code}):The difficulty is {diff}/5 ({diff_label}), workload is {work}/5 ({work_label}), "
    "and sentiment is mostly {sent_label}.{low_n_note}\n{top_tip_line}"
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


SURVEY_DISCLAIMER = (
    "\n\n_This is based on student survey responses, not official course "
    "data, and reflects a small sample -- individual experience may vary._"
)
def _low_n_note(n: int) -> str:
    return LOW_N_NOTE_TEMPLATE if n < LOW_N_THRESHOLD else ""


def _plural(n: int) -> str:
    return "" if n == 1 else "s"


def generate_response(intent: str | None, course_code: str | None, course_index: dict) -> str | None:
    """
    Returns a reply string, or None if this isn't a course query the
    generator can answer (caller should fall through to the nltk Chat).
    """
    if course_code is None:
        if intent is not None:
            return CLARIFY_WHICH_COURSE
        return None  

    info = course_index.get(course_code)
    if info is None:
        return COURSE_NOT_FOUND

    name = info["course_name"]
    intent = intent or "overview"

    if intent == "difficulty":
        if info.get("mean_difficulty") is None:
            return NO_RATING_DATA.format(name=name, code=course_code)
        n = info["n_difficulty_ratings"]
        return DIFFICULTY.format(
            name=name, code=course_code, diff=info["mean_difficulty"],
            diff_label=info["difficulty_label"], n=n, n_plural=_plural(n),
            low_n_note=_low_n_note(n),
        ) + SURVEY_DISCLAIMER

    if intent == "workload":
        if info.get("mean_workload") is None:
            return NO_RATING_DATA.format(name=name, code=course_code)
        n = info["n_workload_ratings"]
        return WORKLOAD.format(
            name=name, code=course_code, work=info["mean_workload"],
            work_label=info["workload_label"], n=n, n_plural=_plural(n),
            low_n_note=_low_n_note(n),
        ) + SURVEY_DISCLAIMER

    if intent == "tips":
        sample_tips = info.get("sample_tips") or []
        if not sample_tips:
            return TIPS_NO_DATA.format(name=name, code=course_code)
        bullet_list = "\n".join(f"- {t}" for t in sample_tips)
        return TIPS_WITH_DATA.format(name=name, sample_tips=bullet_list) + SURVEY_DISCLAIMER

    if intent == "sentiment":
        if info.get("sentiment_label") in (None, "no_data"):
            return SENTIMENT_NO_DATA.format(name=name, code=course_code)
        n_comments = info["n_comments"]
        themes = ", ".join(info.get("themes") or []) or "none identified"
        return SENTIMENT_WITH_DATA.format(
            name=name, sent_label=info["sentiment_label"], pct_pos=info["pct_positive"],
            n_comments=n_comments, n_comments_plural=_plural(n_comments), themes=themes,
        ) + SURVEY_DISCLAIMER

    # overview (default)
    if info.get("mean_difficulty") is None and info.get("mean_workload") is None:
        return NO_RATING_DATA.format(name=name, code=course_code)

    n_diff = info.get("n_difficulty_ratings", 0)
    n_work = info.get("n_workload_ratings", 0)
    low_n = _low_n_note(min(n_diff, n_work)) if (n_diff and n_work) else ""

    sample_tips = info.get("sample_tips") or []
    top_tip_line = f"Tip: {sample_tips[0]}" if sample_tips else "No written tips available yet."

    return OVERVIEW.format(
        name=name, code=course_code,
        diff=info.get("mean_difficulty", "N/A"), diff_label=info.get("difficulty_label", "Unknown"),
        work=info.get("mean_workload", "N/A"), work_label=info.get("workload_label", "Unknown"),
        sent_label=info.get("sentiment_label", "no_data"),
        low_n_note=low_n, top_tip_line=top_tip_line,
    ) + SURVEY_DISCLAIMER

import csv
import json
import re
from pathlib import Path
from typing import Literal
from pipeline.context import PipelineContext, clear_workflow
from .data.courses import COURSE_INDEX, CURRICULUM
from .data.course_aliases import curriculum_code, suggest_courses

def parse_csv_rules(filepath):
    """
    Parses the student rules CSV file and returns a hierarchical dictionary where 
    main rules contain their respective sub-rules.
    """
    rules_dict = {}
    
    try:
        with open(filepath, mode='r', encoding='utf-8-sig') as file:
            # Create a CSV reader object, treating the first row as headers
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                # Extract the fields from the row based on the headers
                section_num = row.get('Section Number', '').strip()
                section_title = row.get('Section Title', '').strip()
                main_rule = row.get('Main Rule', '').strip()
                sub_rule = row.get('Sub-Rule', '').strip()
                rule_text = row.get('Rule Text', '').strip()
                
                # If this main rule is not in our dictionary yet, initialize it
                if main_rule not in rules_dict:
                    rules_dict[main_rule] = {
                        'Section Number': section_num,
                        'Section Title': section_title,
                        'Rule Text': '',
                        'Sub-Rules': {}
                    }
                
                # If there is no sub-rule, this is the main rule's text
                if not sub_rule:
                    rules_dict[main_rule]['Rule Text'] = rule_text
                # If there is a sub-rule, add it to the sub-rules dictionary
                else:
                    rules_dict[main_rule]['Sub-Rules'][sub_rule] = rule_text
                
        return rules_dict

    except FileNotFoundError:
        print(f"Error: The file {filepath} was not found.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None



_DATA = Path(__file__).parent / "data"
RULES = parse_csv_rules(_DATA / "HandbookRules.csv") or {}
INTENT_RESPONSES = json.loads((_DATA / "intent_responses.json").read_text(encoding="utf-8"))


def _eligibility(ctx: PipelineContext) -> str:
    session = ctx.session_state
    slots = session["slots"]
    pending = session.get("pending_slot")
    codes = [curriculum_code(c) for c in ctx.entities.get("course_codes", [])]
    ctx.status = "needs_input"
    prompts = {
        "passed_courses": "Which courses have you passed? List course codes, or say 'none'.",
        "taken_courses": "Which other courses have you previously taken, including failed courses? List course codes, or say 'none'.",
        "current_term": "What term are you enrolling for? Please answer with Term 1, Term 2, or Term 3.",
    }
    if ctx.control_flags.get("repeat_prompt"):
        return prompts.get(pending, "Which course would you like to check eligibility for?")
    if pending in ("passed_courses", "taken_courses"):
        unknown = ctx.entities.get("unknown_courses", [])
        if unknown:
            return "I couldn't recognize these course codes: " + ", ".join(unknown) + ". Please correct them."
        none = re.fullmatch(r"\s*(?:none|no(?: other)? courses|nothing|no)[.! ]*", ctx.normalized_text, re.I)
        if not codes and not none:
            return prompts[pending]
        negated = re.search(r"\b(not|never|didn't|don't|haven't|haven’t|did not|have not)\b", ctx.normalized_text, re.I)
        failed = pending == "passed_courses" and re.search(r"\b(fail|failed|failing)\b", ctx.normalized_text, re.I)
        if codes and (negated or failed):
            return "I haven't added those courses. " + prompts[pending]
        slots[pending] = codes
        session["pending_slot"] = "taken_courses" if pending == "passed_courses" else "current_term"
        return prompts[session["pending_slot"]]
    elif pending == "current_term":
        text = re.sub(r"^(?:actually|correction|instead|i meant)[,: ]*", "", ctx.normalized_text, flags=re.I)
        term = re.fullmatch(r"\s*(?:term\s*)?([1-3])[.! ]*", text, re.I)
        if not term:
            return "Please answer with Term 1, Term 2, or Term 3."
        slots["current_term"] = int(term[1])
        result = CURRICULUM.check_eligibility(slots["target_course"], slots["passed_courses"],
                                              list(set(slots["passed_courses"] + slots.get("taken_courses", []))),
                                              slots["current_term"])
        response = result["message"]
        if result.get("eligible") and result.get("corequisites"):
            response += "\n\nYou must also enroll in: " + ", ".join(result["corequisites"])
        clear_workflow(session)
        ctx.status = "answered"
        return response
    if "target_course" not in slots:
        if not codes:
            session.update(active_workflow="Academic_Eligibility", pending_slot="target_course")
            return "Which course would you like to check eligibility for?"
        if not CURRICULUM.course_exists(codes[0]):
            return "I couldn't find that course in the curriculum. Please check the course code."
        slots["target_course"] = codes[0]
        session.update(active_workflow="Academic_Eligibility", pending_slot="passed_courses")
        return (f"I can help you check your eligibility for {codes[0]}. "
                "Please list the course codes you have already passed, or say 'none'.")
    return "What term are you enrolling for? Please answer with Term 1, Term 2, or Term 3."


def query_domain(ctx: PipelineContext, source: Literal["course", "academic"]) -> str:
    if source not in ("course", "academic"):
        raise ValueError(f"Unknown retrieval source: {source}")
    if source == "academic" and ctx.intent == "eligibility":
        return _eligibility(ctx)
    codes = ctx.entities.get("course_codes", [])
    code = codes[0] if codes else None
    if source == "course":
        if not code:
            suggestions = suggest_courses(ctx.raw_text)
            if suggestions:
                return f"{CLARIFY_WHICH_COURSE} Did you mean: {', '.join(suggestions)}?"
            return CLARIFY_WHICH_COURSE
        if code in COURSE_INDEX:
            return generate_response(ctx.intent, code, COURSE_INDEX)
        return CURRICULUM.describe_course(curriculum_code(code))
    if ctx.intent in ("prerequisites", "offerings"):
        if not code:
            suggestions = suggest_courses(ctx.raw_text)
            if suggestions:
                return f"{CLARIFY_WHICH_COURSE} Did you mean: {', '.join(suggestions)}?"
            return CLARIFY_WHICH_COURSE
        code = curriculum_code(code)
        course = CURRICULUM.get_course(code)
        if not course:
            return COURSE_NOT_FOUND
        if ctx.intent == "offerings":
            return f"{code} ({course['name']}) is normally offered during Term {course['offered_term']}."
        lines = [f"Here are the prerequisites for {code} ({course['name']}):"]
        def describe(codes):
            return ", ".join(f"{c} ({CURRICULUM.get_course_name(c)})" if CURRICULUM.get_course_name(c) else c for c in codes)
        hard = CURRICULUM.get_hard_prerequisites(code)
        lines.append("• Must have passed: " + (describe(hard) if hard else "None (no hard prerequisites)"))
        for label, related in (("Recommended to have taken", CURRICULUM.get_soft_prerequisites(code)),
                               ("Must be taken together", CURRICULUM.get_corequisites(code))):
            if related:
                lines.append(f"• {label}: {describe(related)}")
        return "\n".join(lines)
    if ctx.intent == "handbook":
        rule_id = ctx.entities.get("rule_id")
        rule = RULES.get(rule_id)
        if rule:
            lines = [f"According to the handbook, <b>Section {rule_id}: {rule['Section Title']}</b> states that:\n\n{rule['Rule Text']}"]
            lines.extend(f"<b>{key}</b>: {value}" for key, value in rule["Sub-Rules"].items())
            return "\n\n".join(lines)
    templates = INTENT_RESPONSES.get(ctx.intent)
    if templates:
        return templates[0].format(**ctx.entities)
    return "Please ask about a course, its prerequisites, eligibility, or a handbook policy."


execute_retrieval = query_domain
