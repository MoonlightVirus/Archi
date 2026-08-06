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
from pipeline.intent_classifier import IntentClassifier

# ==========================================================
# 1. NLP Pipeline Initialization
# ==========================================================
_project_root = os.path.dirname(os.path.abspath(__file__))
_pipeline_dir = os.path.join(_project_root, 'pipeline')
_entities_path = os.path.join(_pipeline_dir, 'academic_entities.json')
_binding_path = os.path.join(_pipeline_dir, 'binding_rules.json')
_extractor = FeatureExtractor(json_path=_entities_path, binding_rules_path=_binding_path)

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
# 4. HandbookRules — Mapping from NLP Intents to CSV Rules
# ==========================================================
_csv_path = os.path.join(_project_root, 'references', 'HandbookRules.csv')
_rules_dict = parse_csv_rules(_csv_path) or {}

_intent_rule_map_path = os.path.join(_responses_dir, 'intent_to_rule_map.json')
_classifier = IntentClassifier(intent_rule_map_path=_intent_rule_map_path)

def _format_handbook_rule(rule_id):
    if not _rules_dict or not rule_id or rule_id not in _rules_dict:
        return None
        
    rule_data = _rules_dict[rule_id]
    response = f"According to the handbook, <b>Section {rule_id}: {rule_data['Section Title']}</b> states that:\n\n{rule_data['Rule Text']}\n"
    
    for sub_id, sub_text in rule_data.get('Sub-Rules', {}).items():
        response += f"\n<b>{sub_id}</b>: {sub_text}\n"
        
    return response

def _handle_intent(intent, kwargs):
    """
    Helper function to route intents to their corresponding response templates.
    """
    if intent == 'HANDBOOK_RULE':
        return _format_handbook_rule(kwargs.get('rule_id'))
        
    if intent and intent in INTENT_RESPONSES:
        template = random.choice(INTENT_RESPONSES[intent])
        response = template.format(**kwargs)
        print(response)
        return response
        
    return None

def get_response(user_input: str) -> str:
    """
    Single entry point for the Streamlit frontend.
    """
    if not user_input or not user_input.strip():
        return FALLBACK_RESPONSE

    # Parse inputs using the pipeline
    try:
        preprocessed = preprocess_text(user_input)
        features = _extractor.extract_features(preprocessed)
        
        # Classify intent using the IntentClassifier
        intent, kwargs = _classifier.classify_intent(features)
        
        # Output & Action module routing
        response_text = _handle_intent(intent, kwargs)
        if response_text:
            return response_text
            
    except Exception as e:
        print(f"Pipeline error: {e}")

    # 3. Fallback to Regex for broad catch-alls or numerical inputs
    response = _fallback_chatbot.respond(user_input)
    if response:
        print(response)
        return response
        
    return FALLBACK_RESPONSE
