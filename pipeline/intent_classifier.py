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

        categories = [
            entity.get("category")
            for entity in entities
            if entity.get("category")
        ]

        entity_lookup = {
            entity.get("category"): entity.get("entity")
            for entity in entities
            if entity.get("category")
        }

        # =====================================================
        # 2. Bound actions
        # =====================================================
        for entity in entities:
            if entity.get("type") != "bound_parameter":
                continue

            action = entity.get("action")
            target = entity.get("target_entity")
            target_category = entity.get("target_category")

            if action == "ACTION_FAIL" and target_category == "COURSE_CODE":
                return "ACTION_FAIL", {
                    "target": target.upper() if target else None
                }

            if action == "ACTION_DEFER" and target_category == "COURSE_CODE":
                return "ACTION_DEFER", {
                    "target": target.upper() if target else None
                }

            if action in [
                "ACTION_SCHEDULE",
                "ACTION_RESCHEDULE",
                "CONSULTATION_TERM"
            ]:
                return action, {
                    "target": target
                }

            if action == "ACTION_CANCEL":
                if target_category == "PERSON":
                    return "ACTION_CANCEL", {
                        "target": target
                    }

                if target_category == "COURSE_CODE":
                    return "ACTION_ADVISE", {
                        "action": "drop"
                    }

            if action == "ACTION_ADVISE":
                return "ACTION_ADVISE", {
                    "action": "underload"
                }

        # =====================================================
        # 3. Curriculum intents
        # =====================================================
        course_code = entity_lookup.get("COURSE_CODE")

        if course_code:
            course_code = course_code.upper()

            if "ACTION_FAIL" in categories:
                return "ACTION_FAIL", {
                    "target": course_code
                }

            if "ACTION_DEFER" in categories:
                return "ACTION_DEFER", {
                    "target": course_code
                }

            if "FLOWCHART_TERM" in categories:
                return "PREREQUISITE_CHECK", {
                    "course": course_code
                }

            if "CURRICULUM_ACTION" in categories:
                return "CHECK_ELIGIBILITY", {
                    "course": course_code
                }

            return "COURSE_INFO", {
                "course": course_code
            }

        # =====================================================
        # 4. Flowchart intents
        # =====================================================
        if (
            "ACTION_UPDATE" in categories
            and "FLOWCHART_TERM" in categories
        ):
            return "FLOWCHART_UPDATE", {}

        # =====================================================
        # 5. GPA intents
        # =====================================================
        if "GPA_CALCULATE" in categories:
            return "GPA_CALCULATE", {}

        if "GPA_UNDERSTAND" in categories:
            return "GPA_UNDERSTAND", {}

        if "GPA_LOW_CONCERN" in categories:
            return "GPA_LOW_CONCERN", {}

        if "GPA_IMPROVE" in categories:
            return "GPA_IMPROVE", {}

        # =====================================================
        # 6. Status intent
        # =====================================================
        if "STATUS_CHECK" in categories:
            return "STATUS_CHECK", {
                "target": entity_lookup.get(
                    "COURSE_CODE",
                    "enrollment"
                )
            }

        return None, {}

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
