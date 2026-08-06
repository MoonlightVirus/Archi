import csv
import json
import functools

def parse_csv_rules(filepath):
    """
    Parses the student rules CSV file and returns a hierarchical dictionary where 
    main rules contain their respective sub-rules.
    """
    rules_dict = {}
    
    try:
        with open(filepath, mode='r', encoding='utf-8-sig') as file:
            # Create a CSV reader object, treating the first row as headers
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                # Extract the fields from the row based on the headers
                section_num = row.get('Section Number', '').strip()
                section_title = row.get('Section Title', '').strip()
                main_rule = row.get('Main Rule', '').strip()
                sub_rule = row.get('Sub-Rule', '').strip()
                rule_text = row.get('Rule Text', '').strip()
                
                # If this main rule is not in our dictionary yet, initialize it
                if main_rule not in rules_dict:
                    rules_dict[main_rule] = {
                        'Section Number': section_num,
                        'Section Title': section_title,
                        'Rule Text': '',
                        'Sub-Rules': {}
                    }
                
                # If there is no sub-rule, this is the main rule's text
                if not sub_rule:
                    rules_dict[main_rule]['Rule Text'] = rule_text
                # If there is a sub-rule, add it to the sub-rules dictionary
                else:
                    rules_dict[main_rule]['Sub-Rules'][sub_rule] = rule_text
                
        print(f"Successfully parsed {len(rules_dict)} main rules from {filepath}.")
        return rules_dict

    except FileNotFoundError:
        print(f"Error: The file {filepath} was not found.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# This allows you to test the script directly
if __name__ == '__main__':
    _rules_dict = parse_csv_rules('references/HandbookRules.csv')
    
    for main_rule_num, rule in _rules_dict.items():
        print(f"{main_rule_num}: {rule['Rule Text']}")
        print("Sub-Rules:")
        for sub_id, sub_text in rule['Sub-Rules'].items():
            print(f"  {sub_id}: {sub_text}")
        print()

        