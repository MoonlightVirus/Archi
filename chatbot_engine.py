"""
chatbot_engine.py
------------------
Merged NLTK-based response engine for ARCHI, combining the three
member modules from ARCHI_CHATBOT.ipynb (Louis, Renee, Marthy) into
a single importable Chat instance.

This replaces the notebook's three separate `while True: input()`
CLI loops with one `get_response(user_input)` function that the
Streamlit frontend can call directly from state.py's `bot_reply()`.

Ordering matters for nltk.chat.util.Chat: it returns the FIRST
pattern that matches. Broad catch-alls (e.g. greetings, affirmations,
emotion words wrapped in "(.*)") are placed AFTER narrow, specific
intent patterns (flowchart actions, consultation booking, GPA
calculations) so specific requests aren't swallowed by a generic
pattern first.
"""
from datetime import datetime, date
import os
from nltk.chat.util import Chat, reflections
from references.csv_parser import parse_csv_rules

# ==========================================================
# 1. MARTHY — Flowcharts & Consultation (specific intents)
# ==========================================================
_marthy_pairs = [
    # --- Flowcharts ---
    [r'(.*)(fetch|check|what are)(.*)prerequisite(s)? for (.*)',
     ["ARCHI is fetching the prerequisites for %5 from the database now...",
      "Let ARCHI scan your flowchart for %5... Got it! I've pulled up the prerequisite list for you."]],

    [r'(.*)update(.*)flowchart(.*)',
     ["ARCHI is updating your flowchart based on your recent grades now. All passed subjects have been crossed out!",
      "Sure thing! ARCHI is syncing your grades with your flowchart to make sure it's fully up to date."]],

    [r'(.*)(generate|create)(.*)flowchart(.*)defer(ring)? (.*)',
     ["ARCHI is generating a revised flowchart simulating a deferral for %6... I will adjust your future terms accordingly.",
      "Leave it to ARCHI! I am creating a new flowchart track that defers %6. Let me process the prerequisite shifts..."]],

    [r'(.*)(generate|create)(.*)flowchart(.*)fail(ed)? (.*)',
     ["ARCHI is generating a new flowchart track accounting for a failed grade in %6... You will need to retake it next term.",
      "Don't worry, ARCHI is revising your flowchart due to failing %6. Let me recalculate your prerequisites and graduation timeline."]],

    [r'(.*)suggest(.*)action(.*)(underload|shift|drop)(.*)',
     ["ARCHI is analyzing your current standing... Based on your request to %4, I suggest dropping a minor subject first to balance your load. Generating an optimal plan...",
      "Let ARCHI calculate the best course of action for your %4 request. Suggesting a revised term schedule now..."]],

    # --- Consultation ---
    [r'(.*)(check|find|what are)(.*)(consultation hours|availability) of (.*)',
     ["Let ARCHI look up %5's schedule in the faculty database... Found it! I've pinned their available booking slots to your dashboard.",
      "Checking the department bulletin for %5's consultation hours... Okay, I've got their free time pulled up so we can book."]],

    [r'(.*)(schedule|book|set up)(.*)consultation with (.*)',
     ["As your dedicated consultation bot, ARCHI is checking %4's calendar now... I have successfully booked your consultation and sent you both an invite!",
      "Leave the booking to ARCHI! Done, I've scheduled your academic advising session with %4 and blocked off the time in your calendar."]],

    [r'(.*)(reschedule|move|change)(.*)consultation with (.*)',
     ["ARCHI can help with that! Let me look at %4's alternative slots... Okay, I have proposed a new time for your consultation.",
      "Moving your booking... Done! ARCHI has rescheduled your consultation with %4. I'll notify them of the change."]],

    [r'(.*)(cancel|drop)(.*)consultation(.*)with (.*)',
     ["ARCHI has successfully canceled your consultation with %5. Their calendar slot has been freed up.",
      "Cancellation confirmed! I've removed the consultation with %5 from your schedule. Let me know when you want to book again!"]],
]

# ==========================================================
# 2. RENEE — GPA tracking & calculation (specific intents)
# ==========================================================
_renee_pairs = [
    [r'(.*)(calculate my gpa|what is my gpa|gpa calculation)(.*)',
     ['To calculate your GPA, we need your grades and number of units for each course. Can you provide those?',
      'At DLSU, your GPA is calculated by multiplying each grade by its course credits, adding them up, and dividing that total by your overall credits, rounded to two decimal places.']],

    [r'(.*)(understand gpa|gpa policy|how does gpa work)(.*)',
     ['Our GPA policy is outlined in the student handbook. Would you like me to direct you to that section?',
      'GPA is a weighted average of the grades you earn in your courses.']],

    [r'(.*)(low gpa concern|worried about gpa|gpa is low)(.*)',
     ["I understand. We have academic advisors who can help you improve your GPA. Would you like to schedule a meeting?",
      "Don't worry, there are resources available to help. Let's explore some options together."]],

    [r'I (need|want|have) to (improve|raise|bounce back) my (gpa|cgpa|current GPA)(.*)',
     ["I understand. We have academic advisors who can help you improve your GPA. Would you like to schedule a meeting?",
      "Don't worry, there are resources available to help. Let's explore some options together."]],

    [r'I want to check my (.*) status',
     ['Let me look into your %1 status right away. Please hold on.']],

    [r'.*?(\d+)\s*(?:credits|units).*?([0-3]\.[0-9]|4\.0)\s*(?:gpa|cgpa).*',
     ["Got it. You have %1 units with a %2 CGPA. I've logged this into your profile."]],

    [r'.*(?:target|aim for|want a|want to reach)\s*([0-3]\.[0-9]|4\.0).*',
     ['Target CGPA set to %1. How many units do you have left to take next semester?']],

    [r'.*(\d+)\s*(?:units|credits)\s*(?:left|remaining|next semester).*',
     ['Logged %1 remaining units. Type "optimize" and I\'ve got the math covered for you!']],
]

# These two Renee patterns are intentionally very loose ("grades",
# "optimize") and would otherwise swallow Louis's emotion-recognition
# patterns (e.g. "I'm so stressed about my grades" contains the word
# "grades" but should hit the empathy response, not this one). They're
# kept separate and merged in AFTER Louis's pairs below.
_renee_broad_fallback_pairs = [
    [r'.*(?:optimize|calculate strategy|how do i get there).*',
     ['Processing your academic profile...(soon)']],

    [r'.*(?:TOR|transcript of records|grades).*',
     ['Got it. I will take note of your transcript of records for future reference.']],
]

# ==========================================================
# 3. HandbookRules — References the Handbook rulebook from regex queries
# ==========================================================
_handbookRules = []

# ==========================================================
# 4. LOUIS — Greetings, empathy, enders (broad catch-alls)
#    Kept LAST so they don't swallow the specific intents above.
# ==========================================================
_louis_pairs = [
    [r'(.*)(stressed|panicking|panic|overwhelmed|anxious|failing|delayed)(.*)',
     ["Take a deep breath. Academic journeys can be tough, but you are not alone. Let's look over your flowchart together and find a strategic way forward.",
      "It is completely okay to feel overwhelmed. Archi is here to help you structure your steps. Let's start by looking at your current term tracking to ease the load."]],

    [r'(.*)(confused|lost|dont know what to do|stuck|clueless)(.*)',
     ["Don't worry, navigating your academic path can be complicated! Let's clear up the confusion. What specific prerequisite or term requirement are you looking at?",
      "Let's get you back on track. Tell me what course or consultation process is confusing you, and we will break it down together."]],

    [r'(.*)(thank you|thanks|salamat|ty)(.*)',
     ["You're very welcome! Always glad to help an Archer succeed. Let me know if you need anything else.",
      "Happy to help! Keep pushing forward toward your goals. Animo!"]],

    [r'^(hi|hello|hey|greetings)(.*)$|(.*)\b(hello|hi|hey|greetings|hola|kamusta|whats up|sup|archi)\b(.*)',
     ["Animo! I am Archi, your Intelligent Academic Guide. How can I help you optimize your term today?",
      "Hello! Archi here. Ready to map out your academic path. What can I do for you?"]],

    [r'^(goodbye|bye|see ya|exit)(.*)$',
     ["Goodbye! Have a productive trimester. Remember to track your flowchart regularly!",
      "See you later! Don't hesitate to consult me the next time you need to optimize your grades."]],

    [r'^(okay|mhm|i see|sure|yes)(.*)$',
     ["I'm glad you Understand! Do you have other questions or inquiries?",
      "Let's continue! Do you have other questions or inquiries?",
      "Do you have other questions or inquiries?"]],
]



# ==========================================================
# Merge order: specific intents first, broad catch-alls last
# ==========================================================
ALL_PAIRS = _marthy_pairs + _renee_pairs + _handbookRules + _louis_pairs + _renee_broad_fallback_pairs

_chatbot = Chat(ALL_PAIRS, reflections)

FALLBACK_RESPONSE = (
    "I don't understand, could you please rephrase your request so I can "
    "understand it correctly?"
)


def get_response(user_input: str) -> str:
    """
    Single entry point for the Streamlit frontend.
    Mirrors the notebook's chatbot.respond() call + None fallback,
    but as a plain function instead of a CLI loop.
    """
    if not user_input or not user_input.strip():
        return FALLBACK_RESPONSE

    response = _chatbot.respond(user_input)
    return response if response is not None else FALLBACK_RESPONSE
