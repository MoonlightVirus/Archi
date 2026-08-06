import json
import os
import sys

# Ensure the project root is in the path so we can import from references
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from preprocessor import preprocess_text
from featureExtraction import FeatureExtractor
from references.csv_parser import parse_csv_rules

def test_handbook_rule_retrieval():
    extractor = FeatureExtractor('academic_entities.json')
    
    # Load the rule book
    rulebook_path = os.path.join(project_root, 'references', 'HandbookRules.csv')
    rules = parse_csv_rules(rulebook_path)

    # Comprehensive Chatbot intent-to-rule mapping covering all handbook sections
    intent_to_rule_map = {
        "ACADEMIC_UNIT": "10.1",
        "ACADEMIC_LOAD": "10.2",
        "GRADING_TERM": "10.3",
        "NON_ACADEMIC_GRADING": "10.4",
        "GPA_INCLUSION": "10.5",
        "GPA_TERM": "10.6",
        "CROSS_ENROLLMENT": "10.7",
        "STUDENT_TYPE": "10.8",
        "GPA_ALL_GRADES": "10.9",
        "COURSE_COMPONENT": "10.10",
        "ACTION_CANCEL": "10.11",
        "FINANCIAL_TERM": "10.11",
        "ACTION_PETITION": "10.12",
        "ENROLLMENT_TERM": "10.13",
        "AUDIT_TERM": "10.14",
        "AUDIT_GPA": "10.15",
        "CONVERT_AUDIT": "10.16",
        "RETENTION_TERM": "10.17",
        "MAXIMUM_TENURE": "10.18",
        "NSTP_TERM": "10.19",
        "SPECIAL_COURSE": "10.20",
        "COURSE_EQUIVALENT": "10.21",
        "HONORS_LIST": "11.1",
        "UNIVERSITY_HONORS": "11.2",
        "HONORS_TERM": "11.3",
        "HONORS_ABSENCES": "11.4",
        "HONORS_PASS_FAIL": "11.5",
        "HONORS_CLARIFICATION": "11.6",
        "HONORS_ENROLLMENT": "11.7",
        "GRADUATION_TERM": "12.1",
        "GRADUATION_LAST_TERM": "12.2",
        "JOSE_RIZAL_AWARD": "12.3",
        "GRADUATION_HONORS": "12.4",
        "AWARDS_TERM": "12.5",
        "SPECIAL_AWARDS_GRAD": "12.6",
        "SPECIAL_HONORS_MAJOR": "12.7"
    }

    test_cases = [
        "How much credit is a regular course?",
        "Am I considered on overload if I have 18 units?",
        "What happens if I get a failing grade?",
        "How do I compute my GPA?",
        "Are there special rules for transferee students?",
        "Do I take the laboratory and lecture courses together?",
        "What are the rules for dropping? I want to let go of CCPROG3.",
        "Will I get a refund if I drop?",
        "How can I file a petition for change of grade?",
        "How do I enroll in another section?",
        "Can I audit a class without credit?",
        "Can I shift to another program if I become ineligible?",
        "What happens if I exceed my maximum term?",
        "Do I have to take nstp?",
        "When can I request for a special class?",
        "What are the requirements for the dean list?",
        "Who is eligible for the trimestral honor?",
        "When should I apply for graduation?",
        "What are the requirements for graduating summa cum laude?",
        "Who gets a loyalty award?",
        "How does the pass fail system work for non-academic courses?",
        "Is my term gpa affected by zero credit courses?",
        "Can I cross enroll to another school?",
        "Are all grades gpa included if I shifted programs?",
        "Does my audit class affect my audit gpa?",
        "Is it possible to convert audit to credit?",
        "What is the process to request a course equivalent?",
        "What are the requirements for the university honor list?",
        "Do I get an unlimited absence if I am on the dean list?",
        "How is a pass fail honor computed for my units?",
        "Where can I get clarification honors rules?",
        "Do dean listers get advance enrollment privileges?",
        "What should I do if this is my last term graduation?",
        "How do I become part of the jose rizal society?",
        "Who is eligible for a special award during graduation?",
        "How do I get a department honor for my major?"
    ]

    for i, text in enumerate(test_cases):
        print(f"\n==============================================")
        print(f"--- Test Case {i+1} ---")
        print(f"User Query: \"{text}\"")
        
        preprocessed = preprocess_text(text)
        features = extractor.extract_features(preprocessed)
        
        print("\n[NLP Pipeline] Extracted Intents:")
        extracted_categories = set()
        
        for entity in features['entities']:
            if 'category' in entity:
                cat = entity['category']
                extracted_categories.add(cat)
                print(f" - Found '{entity['entity']}' -> {cat}")
            elif 'action' in entity:
                # Bound parameter
                action = entity['action']
                extracted_categories.add(action)
                print(f" - Found Bound Intent: '{entity['action_entity']}' ({action}) on target '{entity['target_entity']}' ({entity['target_category']})")

        print("\n[Chatbot Engine] Handbook Rule Retrieval:")
        rules_found = False
        matched_rule_ids = set()
        for cat in extracted_categories:
            if cat in intent_to_rule_map:
                rule_id = intent_to_rule_map[cat]
                if rules and rule_id in rules:
                    if rule_id not in matched_rule_ids:
                        matched_rule_ids.add(rule_id)
                        rule_data = rules[rule_id]
                        print(f" > Match! Category {cat} maps to Rule {rule_id}: {rule_data['Section Title']}")
                        print(f"   Excerpt: {rule_data['Rule Text'][:200]}...")
                        if rule_data['Sub-Rules']:
                            print(f"   Includes {len(rule_data['Sub-Rules'])} sub-rules (e.g. {list(rule_data['Sub-Rules'].keys())[0]}).")
                        rules_found = True
        
        if not rules_found:
            print(" > No relevant handbook rules found for this query.")
            
    print(f"\n==============================================\n")

if __name__ == '__main__':
    test_handbook_rule_retrieval()
