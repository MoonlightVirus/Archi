"""
response_generator.py
----------------------
Takes (intent, course_code) plus the merged course index and produces the
final reply string. No regex here -- purely data formatting.
"""
from . import response_templates as tmpl


def _low_n_note(n: int) -> str:
    return tmpl.LOW_N_NOTE_TEMPLATE if n < tmpl.LOW_N_THRESHOLD else ""


def _plural(n: int) -> str:
    return "" if n == 1 else "s"


def generate_response(intent: str | None, course_code: str | None, course_index: dict) -> str | None:
    """
    Returns a reply string, or None if this isn't a course query the
    generator can answer (caller should fall through to the nltk Chat).
    """
    if course_code is None:
        if intent is not None:
            return tmpl.CLARIFY_WHICH_COURSE
        return None  

    info = course_index.get(course_code)
    if info is None:
        return tmpl.COURSE_NOT_FOUND

    name = info["course_name"]
    intent = intent or "overview"

    if intent == "difficulty":
        if info.get("mean_difficulty") is None:
            return tmpl.NO_RATING_DATA.format(name=name, code=course_code)
        n = info["n_difficulty_ratings"]
        return tmpl.DIFFICULTY.format(
            name=name, code=course_code, diff=info["mean_difficulty"],
            diff_label=info["difficulty_label"], n=n, n_plural=_plural(n),
            low_n_note=_low_n_note(n),
        ) + tmpl.SURVEY_DISCLAIMER

    if intent == "workload":
        if info.get("mean_workload") is None:
            return tmpl.NO_RATING_DATA.format(name=name, code=course_code)
        n = info["n_workload_ratings"]
        return tmpl.WORKLOAD.format(
            name=name, code=course_code, work=info["mean_workload"],
            work_label=info["workload_label"], n=n, n_plural=_plural(n),
            low_n_note=_low_n_note(n),
        ) + tmpl.SURVEY_DISCLAIMER

    if intent == "tips":
        sample_tips = info.get("sample_tips") or []
        if not sample_tips:
            return tmpl.TIPS_NO_DATA.format(name=name, code=course_code)
        bullet_list = "\n".join(f"- {t}" for t in sample_tips)
        return tmpl.TIPS_WITH_DATA.format(name=name, sample_tips=bullet_list) + tmpl.SURVEY_DISCLAIMER

    if intent == "sentiment":
        if info.get("sentiment_label") in (None, "no_data"):
            return tmpl.SENTIMENT_NO_DATA.format(name=name, code=course_code)
        n_comments = info["n_comments"]
        themes = ", ".join(info.get("themes") or []) or "none identified"
        return tmpl.SENTIMENT_WITH_DATA.format(
            name=name, sent_label=info["sentiment_label"], pct_pos=info["pct_positive"],
            n_comments=n_comments, n_comments_plural=_plural(n_comments), themes=themes,
        ) + tmpl.SURVEY_DISCLAIMER

    # overview (default)
    if info.get("mean_difficulty") is None and info.get("mean_workload") is None:
        return tmpl.NO_RATING_DATA.format(name=name, code=course_code)

    n_diff = info.get("n_difficulty_ratings", 0)
    n_work = info.get("n_workload_ratings", 0)
    low_n = _low_n_note(min(n_diff, n_work)) if (n_diff and n_work) else ""

    sample_tips = info.get("sample_tips") or []
    top_tip_line = f"Tip: {sample_tips[0]}" if sample_tips else "No written tips available yet."

    return tmpl.OVERVIEW.format(
        name=name, code=course_code,
        diff=info.get("mean_difficulty", "N/A"), diff_label=info.get("difficulty_label", "Unknown"),
        work=info.get("mean_workload", "N/A"), work_label=info.get("workload_label", "Unknown"),
        sent_label=info.get("sentiment_label", "no_data"),
        low_n_note=low_n, top_tip_line=top_tip_line,
    ) + tmpl.SURVEY_DISCLAIMER