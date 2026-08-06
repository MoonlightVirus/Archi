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
_intent_responses_path = os.path.join(_pipeline_dir, 'intent_responses.json')
with open(_intent_responses_path, 'r') as f:
    INTENT_RESPONSES = json.load(f)

# ==========================================================
# 3. FALLBACK REGEX PAIRS (NLTK Chat)
# ==========================================================
_fallback_pairs_path = os.path.join(_pipeline_dir, 'fallback_regex_pairs.json')
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

_intent_rule_map_path = os.path.join(_pipeline_dir, 'intent_to_rule_map.json')
with open(_intent_rule_map_path, 'r') as f:
    intent_to_rule_map = json.load(f)

def extract_intent_and_entities(features):
    """
    Translates NLP pipeline extracted entities into an intent and entity dictionary
    for the template responses.
    """
    entities = features.get('entities', [])
    
    # 1. Check bound parameters (action + target)
    for e in entities:
        if e.get('type') == 'bound_parameter':
            action = e.get('action')
            target = e.get('target_entity')
            target_cat = e.get('target_category')
            
            if action in ['ACTION_SCHEDULE', 'ACTION_RESCHEDULE', 'ACTION_DEFER', 'ACTION_FAIL', 'CONSULTATION_TERM']:
                return action, {'target': target}
            elif action == 'ACTION_CANCEL':
                if target_cat == 'PERSON':
                    return 'ACTION_CANCEL', {'target': target}
                elif target_cat == 'COURSE_CODE':
                    return 'ACTION_ADVISE', {'action': 'drop'}
                return 'ACTION_CANCEL', {'target': target}
            elif action == 'ACTION_ADVISE':
                return 'ACTION_ADVISE', {'action': 'underload'}
                
    # 2. Check independent entities
    categories = [e.get('category') for e in entities if 'category' in e]
    entity_texts = {e.get('category'): e.get('entity') for e in entities if 'category' in e}
    
    if 'ACTION_UPDATE' in categories and 'FLOWCHART_TERM' in categories:
        return 'FLOWCHART_UPDATE', {}
        
    if 'FLOWCHART_TERM' in categories and 'COURSE_CODE' in categories:
        if "prerequisite" in entity_texts.get('FLOWCHART_TERM', '').lower():
            return 'PREREQUISITE_CHECK', {'target': entity_texts['COURSE_CODE']}
            
    if 'GPA_CALCULATE' in categories: return 'GPA_CALCULATE', {}
    if 'GPA_UNDERSTAND' in categories: return 'GPA_UNDERSTAND', {}
    if 'GPA_LOW_CONCERN' in categories: return 'GPA_LOW_CONCERN', {}
    if 'GPA_IMPROVE' in categories: return 'GPA_IMPROVE', {}
    if 'STATUS_CHECK' in categories:
        target = entity_texts.get('COURSE_CODE', 'enrollment')
        return 'STATUS_CHECK', {'target': target}
        
    return None, {}

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
        
        # 1. Check for Handbook Rules directly
        extracted_categories = set()
        for entity in features.get('entities', []):
            if 'category' in entity:
                extracted_categories.add(entity['category'])
            elif 'action' in entity:
                extracted_categories.add(entity['action'])
                
        for cat in extracted_categories:
            if cat in intent_to_rule_map:
                rule_id = intent_to_rule_map[cat]
                if _rules_dict and rule_id in _rules_dict:
                    rule_data = _rules_dict[rule_id]
                    response_text = f"According to the handbook, <b>Section {rule_id}: {rule_data['Section Title']}</b> states that:\n\n{rule_data['Rule Text']}\n"
                    if rule_data.get('Sub-Rules'):
                        for sub_id, sub_text in rule_data['Sub-Rules'].items():
                            response_text += f"\n<b>{sub_id}</b>: {sub_text}\n"
                    return response_text
        
        # 2. Check Intent Responses
        intent, entity_kwargs = extract_intent_and_entities(features)
        if intent and intent in INTENT_RESPONSES:
            template = random.choice(INTENT_RESPONSES[intent])
            response = template.format(**entity_kwargs)
            print(response)
            return response
            
    except Exception as e:
        print(f"Pipeline error: {e}")

    # 3. Fallback to Regex for broad catch-alls or numerical inputs
    response = _fallback_chatbot.respond(user_input)
    if response:
        print(response)
        return response
        
    return FALLBACK_RESPONSE
