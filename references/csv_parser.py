import csv
import json
import functools

def parse_csv_rules(filepath):
    """
    Parses the student rules CSV file and returns the data.
    Demonstrates reading and structuring the data.
    """
    rules_data = []
    
    try:
        with open(filepath, mode='r', encoding='utf-8') as file:
            # Create a CSV reader object, treating the first row as headers
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                # Extract the fields from the row based on the headers
                section_num = row.get('Section Number', '').strip()
                section_title = row.get('Section Title', '').strip()
                main_rule = row.get('Main Rule', '').strip()
                sub_rule = row.get('Sub-Rule', '').strip()
                rule_text = row.get('Rule Text', '').strip()
                
                # Append the parsed data as a dictionary to the list
                rules_data.append({
                    'Section Number': section_num,
                    'Section Title': section_title,
                    'Main Rule': main_rule,
                    'Sub-Rule': sub_rule,
                    'Rule Text': rule_text
                })
                
        print(f"Successfully parsed {len(rules_data)} rules from {filepath}.")
        return rules_data

    except FileNotFoundError:
        print(f"Error: The file {filepath} was not found.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# Helper function to group rules by section
def _group_rules_by_section(rules_data):
    """Groups parsed CSV data by main rule and section."""
    grouped_rules = {}
    for r in rules_data:
        rule_text = r.get('Rule Text', '').strip()
        if not rule_text:
            continue
            
        main_rule = r.get('Main Rule', '').strip()
        sub_rule = r.get('Sub-Rule', '').strip()
        section_num = r.get('Section Number', '').strip()
        section_title = r.get('Section Title', '').strip()
        
        key = (main_rule, section_num, section_title)
        
        if key not in grouped_rules:
            grouped_rules[key] = {'main_text': '', 'sub_rules': []}
            
        if not sub_rule:
            grouped_rules[key]['main_text'] = rule_text
        else:
            grouped_rules[key]['sub_rules'].append((sub_rule, rule_text))
            
    return grouped_rules

# Helper function to format a single grouped rule
def _format_rule_group(main_rule, section_num, section_title, data):
    """Formats a single grouped rule into a string response."""
    response_lines = [f"{section_title}"]
    
    if data['main_text']:
        response_lines.append(f"Rule: {data['main_text']}")
        
    for sub, text in data['sub_rules']:
        response_lines.append(f"  - {sub}: {text}")
        
    return "\n".join(response_lines).replace("%", " percent")

# Helper function to categorize formatted rules 
def _categorize_formatted_rules(grouped_rules):
    """Categorizes formatted strings into specific rule categories."""
    _ruleCreditGradingRetention = []
    _ruleTrimestralHonors = []
    _ruleGraduation = []
    
    for (main_rule, section_num, section_title), data in grouped_rules.items():
        response_str = _format_rule_group(main_rule, section_num, section_title, data)
        
        if "Credit, Grading, and Retention" in section_title:
            _ruleCreditGradingRetention.append(response_str)
        elif "Trimestral Honors" in section_title:
            _ruleTrimestralHonors.append(response_str)
        elif "Graduation" in section_title:
            _ruleGraduation.append(response_str)
            
    return _ruleCreditGradingRetention, _ruleTrimestralHonors, _ruleGraduation

# Main function to parse and format the rules (cached for performance)
@functools.lru_cache(maxsize=1)
def get_formatted_rules(filepath):
    """
    Parses the student rules CSV file and formats them into a list of strings
    suitable for chatbot responses.
    """
    rules_data = parse_csv_rules(filepath)
    if not rules_data:
        return []

    grouped_rules = _group_rules_by_section(rules_data)
    return _categorize_formatted_rules(grouped_rules)

@functools.lru_cache(maxsize=1)
def get_rules_dict(filepath):
    """
    Parses the student rules CSV file and returns a dictionary mapping
    the main rule number (e.g., '10.1') to its formatted text string.
    """
    rules_data = parse_csv_rules(filepath)
    if not rules_data:
        return {}

    grouped_rules = _group_rules_by_section(rules_data)
    
    formatted_dict = {}
    for (main_rule, section_num, section_title), data in grouped_rules.items():
        formatted_dict[main_rule] = _format_rule_group(main_rule, section_num, section_title, data)
        
    return formatted_dict

# This allows you to test the script directly
if __name__ == '__main__':
    _rules_dict = get_rules_dict('references/HandbookRules.csv')
    
    for key, value in _rules_dict.items():
        print(key, value)
        print()