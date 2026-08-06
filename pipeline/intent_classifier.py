import json

class IntentClassifier:
    def __init__(self, intent_rule_map_path: str):
        with open(intent_rule_map_path, 'r') as f:
            self.intent_to_rule_map = json.load(f)

    def classify_intent(self, features: dict):
        """
        Translates NLP pipeline extracted entities into a standardized intent label 
        and entity dictionary for the response engine.
        """
        entities = features.get('entities', [])
        
        # 1. Check for Handbook Rule intents first
        intent, data = self._check_handbook_rules(entities)
        if intent:
            return intent, data

        # 2. Check bound parameters (action + target)
        intent, data = self._check_bound_parameters(entities)
        if intent:
            return intent, data
            
        # 3. Check independent entities
        return self._check_independent_entities(entities)

    def _check_handbook_rules(self, entities: list):
        extracted_categories = set()
        for entity in entities:
            if 'category' in entity:
                extracted_categories.add(entity['category'])
            elif 'action' in entity:
                extracted_categories.add(entity['action'])
                
        for cat in extracted_categories:
            if cat in self.intent_to_rule_map:
                return 'HANDBOOK_RULE', {'rule_id': self.intent_to_rule_map[cat]}
                
        return None, {}

    def _check_bound_parameters(self, entities: list):
        for e in entities:
            if e.get('type') != 'bound_parameter':
                continue
                
            action = e.get('action')
            target = e.get('target_entity')
            target_cat = e.get('target_category')
            
            if action in ['ACTION_SCHEDULE', 'ACTION_RESCHEDULE', 'ACTION_DEFER', 'ACTION_FAIL', 'CONSULTATION_TERM']:
                return action, {'target': target}
            
            if action == 'ACTION_CANCEL':
                if target_cat == 'COURSE_CODE':
                    return 'ACTION_ADVISE', {'action': 'drop'}
                return 'ACTION_CANCEL', {'target': target}
                
            if action == 'ACTION_ADVISE':
                return 'ACTION_ADVISE', {'action': 'underload'}
                
        return None, {}

    def _check_independent_entities(self, entities: list):
        categories = set(e.get('category') for e in entities if 'category' in e)
        entity_texts = {e.get('category'): e.get('entity') for e in entities if 'category' in e}
        
        if 'ACTION_UPDATE' in categories and 'FLOWCHART_TERM' in categories:
            return 'FLOWCHART_UPDATE', {}
            
        if 'FLOWCHART_TERM' in categories and 'COURSE_CODE' in categories:
            if "prerequisite" in entity_texts.get('FLOWCHART_TERM', '').lower():
                return 'PREREQUISITE_CHECK', {'target': entity_texts['COURSE_CODE']}
                
        for gpa_intent in ['GPA_CALCULATE', 'GPA_UNDERSTAND', 'GPA_LOW_CONCERN', 'GPA_IMPROVE']:
            if gpa_intent in categories:
                return gpa_intent, {}
                
        if 'STATUS_CHECK' in categories:
            target = entity_texts.get('COURSE_CODE', 'enrollment')
            return 'STATUS_CHECK', {'target': target}
            
        return None, {}
