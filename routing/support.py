import re

def distress(text):
    if re.search(r"\b(suicid\w*|self[- ]harm|kill myself|hurt myself|end my life|end myself|(?:do not|don't) want to live)\b", text, re.I):
        return ['crisis']
    if re.search(r"\b(?:i(?: am|'m| feel)? (?:so )?(?:hopeless|worthless|depressed|overwhelmed|a failure)|i want to give up)\b", text, re.I):
        return ['academic_distress']
    return []

def support_reply(kind):
    if kind == 'crisis':
        return ("I'm sorry you're in so much pain. Are you in immediate danger or have you already hurt yourself? "
                "Please reach out to someone you trust who can stay with you. If you may act on these thoughts soon, "
                "contact local emergency services or go to the nearest emergency department.")
    return "That sounds overwhelming. Let's take one step at a time. What's been hardest: a course, your GPA, or planning your term? Your advisor or university counseling service can also support you."
