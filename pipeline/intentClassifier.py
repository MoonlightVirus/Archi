"""
intentClassifier.py

Receives extracted entities from the NLP pipeline and determines
the user's intent.

Returns:
    (intent_name, parameters)
"""


def classify(features):
    entities = features.get("entities", [])

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
    # 1. Bound actions
    # =====================================================

    for entity in entities:
        if entity.get("type") != "bound_parameter":
            continue

        action = entity.get("action")
        target = entity.get("target_entity")
        target_category = entity.get("target_category")

        if action == "ACTION_FAIL" and target_category == "COURSE_CODE":
            return "ACTION_FAIL", {
                "target": target.upper()
            }

        if action == "ACTION_DEFER" and target_category == "COURSE_CODE":
            return "ACTION_DEFER", {
                "target": target.upper()
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
    # 2. Curriculum intents
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
    # 3. Flowchart intents
    # =====================================================

    if (
        "ACTION_UPDATE" in categories
        and "FLOWCHART_TERM" in categories
    ):
        return "FLOWCHART_UPDATE", {}

    # =====================================================
    # 4. GPA intents
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
    # 5. Status intent
    # =====================================================

    if "STATUS_CHECK" in categories:
        return "STATUS_CHECK", {
            "target": entity_lookup.get(
                "COURSE_CODE",
                "enrollment"
            )
        }

    return None, {}