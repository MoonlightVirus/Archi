"""Upstream support responses, evaluated before workflow routing."""

CRISIS_RESPONSE = "I'm really sorry you're feeling this much pain. Your safety matters more than your grades or curriculum right now.\n\nAre you in immediate danger, or have you already taken any steps to hurt yourself?\n\nPlease reach out to someone you trust who can stay with you, such as a family member, friend, counselor, professor, or campus support staff. If you may act on these thoughts soon, contact local emergency services or go to the nearest emergency department."

DISTRESS_RESPONSE = "I'm sorry you're feeling this way — academic setbacks can feel really heavy, but they don't define who you are or what you're capable of.\n\nLet's take it one step at a time. Tell me what's been hardest for you — a specific course, your GPA, or your flowchart — and I'll help you put together a plan to get back on track.\n\nYou don't have to figure this out alone. Your advisor, the university counseling services, and your support network are all here for you too."

def support_response(ctx):
    return CRISIS_RESPONSE if ctx.control_flags.get("crisis") else DISTRESS_RESPONSE
