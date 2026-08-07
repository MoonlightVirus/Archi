"""
chatbot_engine.py
------------------
Refactored NLP-based response engine for ARCHI.
Uses an Intent-to-Response dictionary architecture for mapped intents,
while keeping NLTK Chat purely for broad fallback patterns (emotions, greetings).
"""
from datetime import datetime, date
import os
import random
import json
from nltk.chat.util import Chat, reflections
from references.csv_parser import parse_csv_rules
from pipeline.preprocessor import preprocess_text
from pipeline.featureExtraction import FeatureExtractor
#added by chael
import re
from pipeline.curriculum_engine import CurriculumEngine
#end
from pipeline.intent_classifier import IntentClassifier
#rene
from nlu.course_lookup import COURSE_INDEX
from nlu.entity_extractor import extract_course
from nlu.intent_classifier import classify_intent
from dialogue.response_generator import generate_response
#end

# ==========================================================
# 1. NLP Pipeline Initialization
# ==========================================================
_project_root = os.path.dirname(os.path.abspath(__file__))
_pipeline_dir = os.path.join(_project_root, 'pipeline')
_entities_path = os.path.join(_pipeline_dir, 'academic_entities.json')
_binding_path = os.path.join(_pipeline_dir, 'binding_rules.json')
_extractor = FeatureExtractor(json_path=_entities_path, binding_rules_path=_binding_path)
#added by chael
_curriculum = CurriculumEngine()
# Stores temporary curriculum conversation information.
# This is shared only for the current running session.
_curriculum_context = {
    "waiting_for": None,
    "target_course": None,
    "passed_courses": []
}
#end
# ==========================================================
# 2. INTENT RESPONSES (NLG Dictionary)
# ==========================================================
_responses_dir = os.path.join(_project_root, 'responses')
_intent_responses_path = os.path.join(_responses_dir, 'intent_responses.json')
with open(_intent_responses_path, 'r') as f:
    INTENT_RESPONSES = json.load(f)

# ==========================================================
# 3. FALLBACK REGEX PAIRS (NLTK Chat)
# ==========================================================
_fallback_pairs_path = os.path.join(_responses_dir, 'fallback_regex_pairs.json')
with open(_fallback_pairs_path, 'r') as f:
    _fallback_pairs = json.load(f)

_fallback_chatbot = Chat(_fallback_pairs, reflections)

FALLBACK_RESPONSE = (
    "I don't understand, could you please rephrase your request so I can "
    "understand it correctly?"
)

# ==========================================================
# 4a. Greetings (checked early so "hi archi" isn't mistaken
#     for a course-code query like CBARCHI)
# ==========================================================
_GREETING_RE = re.compile(
    r"^(hi|hello|hey|greetings|hola|kamusta|whats up|sup)(.*)$|"
    r"\b(hi|hello|hey|greetings|hola|kamusta)\b.*\barchi\b",
    re.IGNORECASE,
)

_GREETING_RESPONSES = [
    "Animo! I am Archi, your Intelligent Academic Guide. How can I help you "
    "optimize your term today?\n\nHere are some examples of what you can ask me:\n"
    "\u2022 \"How hard is CBALGCM?\"\n"
    "\u2022 \"Check my eligibility for CCDSTRU\"\n"
    "\u2022 \"What are the prerequisites for CSOPESY?\"",
    "Hello! Archi here. Ready to map out your academic path. What can I do for "
    "you?\n\nTry asking me things like:\n"
    "\u2022 \"Tell me about the handbook rule on dropping a course\"\n"
    "\u2022 \"Book a consultation with an advisor\"\n"
    "\u2022 \"What courses should I take next term?\"",
]


def _try_greeting(user_input: str) -> str | None:
    """Return a greeting response if the input looks like a greeting."""
    if _GREETING_RE.match(user_input):
        return random.choice(_GREETING_RESPONSES)
    return None

# ==========================================================
# 4. HandbookRules — Mapping from NLP Intents to CSV Rules
# ==========================================================
_csv_path = os.path.join(_project_root, 'references', 'HandbookRules.csv')
_rules_dict = parse_csv_rules(_csv_path) or {}

_intent_rule_map_path = os.path.join(_responses_dir, 'intent_to_rule_map.json')
_classifier = IntentClassifier(intent_rule_map_path=_intent_rule_map_path)


#added by chael
def _handle_curriculum_flow(user_input: str, features: dict):
    """
    Handle an ongoing curriculum-planning conversation.

    Returns a response string if the curriculum flow consumed
    the user's input, or None to let the caller continue with
    other handlers.
    """

    # --- Crisis response (always checked first) ---
    categories = {
        entity.get("category")
        for entity in features.get("entities", [])
        if entity.get("category")
    }

    if "CRISIS_TERM" in categories:
        # Cancel any pending curriculum flow.
        _curriculum_context["waiting_for"] = None
        _curriculum_context["target_course"] = None
        _curriculum_context["passed_courses"] = []

        return (
            "I'm really sorry you're feeling this much pain. "
            "Your safety matters more than your grades or curriculum right now.\n\n"
            "Are you in immediate danger, or have you already taken any steps "
            "to hurt yourself?\n\n"
            "Please reach out to someone you trust who can stay with you, "
            "such as a family member, friend, counselor, professor, or campus "
            "support staff. If you may act on these thoughts soon, contact "
            "local emergency services or go to the nearest emergency department."
        )

    # --- Academic distress (non-crisis) ---
    if "ACADEMIC_DISTRESS" in categories:
        # Cancel any pending curriculum flow.
        _curriculum_context["waiting_for"] = None
        _curriculum_context["target_course"] = None
        _curriculum_context["passed_courses"] = []

        return (
            "I'm sorry you're feeling this way — academic setbacks can feel "
            "really heavy, but they don't define who you are or what you're "
            "capable of.\n\n"
            "Let's take it one step at a time. Tell me what's been hardest "
            "for you — a specific course, your GPA, or your flowchart — and "
            "I'll help you put together a plan to get back on track.\n\n"
            "You don't have to figure this out alone. Your advisor, the "
            "university counseling services, and your support network are all "
            "here for you too."
        )

    # --- Step: collect passed courses ---
    if _curriculum_context["waiting_for"] == "passed_courses":
        passed_courses = _classifier.extract_course_codes(features)

        if not passed_courses:
            return (
                "I couldn't identify any course codes in your answer. "
                "Please list the courses you have passed using their codes, "
                "such as CBPROG1, CBPROG2, and CCDSTRU."
            )

        _curriculum_context["passed_courses"] = passed_courses
        _curriculum_context["waiting_for"] = "current_term"

        return (
            "Thank you. What term are you currently enrolling for? "
            "Please answer with Term 1, Term 2, or Term 3."
        )

    # --- Step: collect current term and run eligibility check ---
    if _curriculum_context["waiting_for"] == "current_term":
        term_match = re.search(
            r"\b(?:term\s*)?([1-3])\b",
            user_input.lower()
        )

        if not term_match:
            return (
                "I couldn't determine the term. "
                "Please answer with Term 1, Term 2, or Term 3."
            )

        current_term = int(term_match.group(1))
        course_code = _curriculum_context["target_course"]
        passed_courses = _curriculum_context["passed_courses"]

        # Every passed course has also been taken.
        taken_courses = passed_courses.copy()

        result = _curriculum.check_eligibility(
            course_code,
            passed_courses,
            taken_courses,
            current_term
        )

        response = result["message"]

        if result.get("eligible"):
            corequisites = result.get("corequisites", [])

            if corequisites:
                response += (
                        "\n\nPlease remember that you must also enroll in: "
                        + ", ".join(corequisites)
                )

        # Clear the conversation after completing the check.
        _curriculum_context["waiting_for"] = None
        _curriculum_context["target_course"] = None
        _curriculum_context["passed_courses"] = []

        return response

    return None
#end

#renee
def _try_course_intent_query(user_input: str) -> str | None:
    """
    Tier 1 (runs BEFORE nltk Chat): only fires when the message has a clear,
    narrow intent keyword (difficulty/workload/tips/sentiment -- see
    nlu/intent_classifier.py). These phrasings ("how hard is CBALGCM",
    "workload for CBOPESY") don't overlap with any existing Marthy/Renee/
    Louis pattern, so it's safe to answer them immediately.

    Deliberately does NOT fire on a bare course-code mention with no intent
    keyword (e.g. "check prerequisites for CBALGCM") -- that must still
    reach the existing pairs below undisturbed. See _try_course_overview_fallback.
    """
    intent = classify_intent(user_input)
    if intent is None:
        return None
    course_code = extract_course(user_input, COURSE_INDEX)
    return generate_response(intent, course_code, COURSE_INDEX)

def _try_course_overview_fallback(user_input: str) -> str | None:
    """
    Tier 3 (runs AFTER nltk Chat finds no match): if the message names a
    real course but nothing else matched (no intent keyword, no Marthy/
    Renee/Louis pattern), give a data-backed course overview instead of
    the generic FALLBACK_RESPONSE. Handles bare mentions like
    "tell me about CBALGCM" or just "CBALGCM".
    """
    course_code = extract_course(user_input, COURSE_INDEX)
    if course_code is None:
        return None
    return generate_response(None, course_code, COURSE_INDEX)
#end

def get_response(user_input: str) -> str:
    """
    Single entry point for the Streamlit frontend.
    """
    if not user_input or not user_input.strip():
        return FALLBACK_RESPONSE

    greeting_response = _try_greeting(user_input)
    if greeting_response is not None:
        return greeting_response

    course_response = _try_course_intent_query(user_input)
    if course_response is not None:
        return course_response

    # Parse inputs using the pipeline
    try:
        preprocessed = preprocess_text(user_input)
        features = _extractor.extract_features(preprocessed)

        # Handle curriculum conversation flow (crisis, passed courses, term)
        curriculum_response = _handle_curriculum_flow(user_input, features)
        if curriculum_response is not None:
            return curriculum_response
        # Check intents via IntentClassifier
        intent, entity_kwargs = _classifier.classify_intent(features)
        
        if intent == 'HANDBOOK_RULE':
            rule_id = entity_kwargs.get('rule_id')
            if _rules_dict and rule_id in _rules_dict:
                rule_data = _rules_dict[rule_id]
                response_text = f"According to the handbook, <b>Section {rule_id}: {rule_data['Section Title']}</b> states that:\n\n{rule_data['Rule Text']}\n"
                if rule_data.get('Sub-Rules'):
                    for sub_id, sub_text in rule_data['Sub-Rules'].items():
                        response_text += f"\n<b>{sub_id}</b>: {sub_text}\n"
                return response_text

        #added by chael
        if intent == "CHECK_ELIGIBILITY":
            course_code = entity_kwargs["target"].upper()

            _curriculum_context["target_course"] = course_code
            _curriculum_context["waiting_for"] = "passed_courses"
            _curriculum_context["passed_courses"] = []

            return (
                f"I can help you check your eligibility for {course_code}. "
                "Please list the course codes you have already passed.\n\n"
                "Example: CBPROG1, CBPROG2, CCDSTRU"
            )
        #end
        if intent and intent in INTENT_RESPONSES:
            template = random.choice(INTENT_RESPONSES[intent])
            response = template.format(**entity_kwargs)
            print(response)
            return response

    except Exception as e:
        print(f"Pipeline error: {e}")

    overview_response = _try_course_overview_fallback(user_input)
    if overview_response is not None:
        return overview_response
        
    response = _fallback_chatbot.respond(user_input)
    if response:
        print(response)
        return response

    return FALLBACK_RESPONSE