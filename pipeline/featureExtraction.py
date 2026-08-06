import json
import os
import re
from nltk.tree import Tree

class FeatureExtractor:
    def __init__(self, json_path='academic_entities.json', binding_rules_path='binding_rules.json'):
        self.entity_dict = self._load_json(json_path)
        binding_data = self._load_json(binding_rules_path)
        self.binding_rules = binding_data.get('bindings', [])
        self.syntactical_constraints = binding_data.get('syntactical_constraints', {})
        
        # Create an inverted dictionary: lowercase n-gram phrase -> category
        self.phrase_to_category = {}
        self.max_ngram = 1
        for category, phrases in self.entity_dict.items():
            for phrase in phrases:
                lower_phrase = phrase.lower()
                phrase_set = frozenset(lower_phrase.split())
                self.phrase_to_category[phrase_set] = category
                phrase_len = len(phrase_set)
                if phrase_len > self.max_ngram:
                    self.max_ngram = phrase_len

    def _load_json(self, json_path):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(current_dir, json_path)
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def extract_features(self, preprocessed_data):
        tokens = preprocessed_data['tokens']
        pos_tags = preprocessed_data['pos_tags']
        named_entities = preprocessed_data['named_entities']
        cleaned_tokens = preprocessed_data['cleaned_tokens']
        cleaned_token_indices = preprocessed_data['cleaned_token_indices']

        extracted_entities = []
        matched_cleaned_indices = set()
        matched_token_indices = set()

        # 1. Dictionary Matching
        # Construct N overlapping sequences from max_ngram down to 1
        for n in range(self.max_ngram, 0, -1):
            for i in range(len(cleaned_tokens) - n + 1):
                # Prevent sub-phrases from matching if a longer n-gram already matched
                if all((i + j) in matched_cleaned_indices for j in range(n)):
                    continue
                
                ngram_tokens = cleaned_tokens[i:i+n]
                ngram_set = frozenset(t.lower() for t in ngram_tokens)
                
                if len(ngram_set) != n:
                    continue
                
                if ngram_set in self.phrase_to_category:
                    category = self.phrase_to_category[ngram_set]
                    orig_indices = [cleaned_token_indices[i+j] for j in range(n)]
                    
                    # 2. Syntactical Disambiguation: Keyword Overlap
                    if self._validate_pos_constraints(category, ngram_tokens, orig_indices, pos_tags):
                        ngram_phrase = " ".join(ngram_tokens).lower()
                        extracted_entities.append({
                            'entity': ngram_phrase,
                            'category': category,
                            'indices': orig_indices,
                            'source': 'dictionary'
                        })
                        for j in range(n):
                            matched_cleaned_indices.add(i + j)
                        matched_token_indices.update(orig_indices)

        # 3. Named Entity Recognition (NER)
        current_token_idx = 0
        for chunk in named_entities:
            if isinstance(chunk, Tree):
                label = chunk.label()
                chunk_leaves = chunk.leaves()
                chunk_len = len(chunk_leaves)
                
                if label in ['PERSON', 'ORGANIZATION']:
                    is_matched = any((current_token_idx + j) in matched_token_indices for j in range(chunk_len))
                    if not is_matched:
                        entity_text = " ".join([leaf[0] for leaf in chunk_leaves])
                        orig_indices = list(range(current_token_idx, current_token_idx + chunk_len))
                        extracted_entities.append({
                            'entity': entity_text,
                            'category': label,
                            'indices': orig_indices,
                            'source': 'ner'
                        })
                        matched_token_indices.update(orig_indices)
                current_token_idx += chunk_len
            else:
                current_token_idx += 1

        # Sort extracted entities by their position in the text
        extracted_entities.sort(key=lambda x: x['indices'][0])
        
        # 4. Parameter Binding
        bound_entities = []
        skip_next = False
        for i in range(len(extracted_entities)):
            if skip_next:
                skip_next = False
                continue
                
            curr = extracted_entities[i]
            if i + 1 < len(extracted_entities):
                nxt = extracted_entities[i+1]
                
                # Check against binding rules
                bound = False
                for rule in self.binding_rules:
                    if curr['category'] == rule['action_category'] and nxt['category'] == rule['target_category']:
                        # Ensure proximity
                        if curr['indices'][-1] < nxt['indices'][0]:
                            curr_pos = pos_tags[curr['indices'][-1]][1]
                            nxt_pos = pos_tags[nxt['indices'][0]][1]
                            
                            action_pos_prefixes = rule.get('action_pos', [])
                            target_pos_prefixes = rule.get('target_pos', [])
                            
                            valid_action = not action_pos_prefixes or any(curr_pos.startswith(p) for p in action_pos_prefixes)
                            valid_target = not target_pos_prefixes or any(nxt_pos.startswith(p) for p in target_pos_prefixes)
                            
                            if valid_action and valid_target:
                                bound_entities.append({
                                    'action': curr['category'],
                                    'action_entity': curr['entity'],
                                    'target_category': nxt['category'],
                                    'target_entity': nxt['entity'],
                                    'indices': curr['indices'] + nxt['indices'],
                                    'type': 'bound_parameter'
                                })
                                bound = True
                                skip_next = True
                                break
                
                if bound:
                    continue
            
            bound_entities.append(curr)
            
        # 5. Dynamic Course Codes
        all_matched_indices = set()
        for e in bound_entities:
            all_matched_indices.update(e['indices'])
            
        dynamic_course_codes = []
        for i, token in enumerate(tokens):
            if i in all_matched_indices:
                continue
                
            # Pattern: alphanumeric density (letters and numbers) and capitalization
            if re.match(r'^(?=.*[a-zA-Z])(?=.*\d)[a-zA-Z\d]+$', token) and any(c.isupper() for c in token):
                # Check adjacency to ENROLLMENT_TERM or GRADING_TERM
                is_adjacent = False
                for e in bound_entities:
                    cat = e.get('category')
                    if cat in ['ENROLLMENT_TERM', 'GRADING_TERM']:
                        dist = min(abs(i - idx) for idx in e['indices'])
                        if dist <= 3:
                            is_adjacent = True
                            break
                            
                if is_adjacent:
                    dynamic_course_codes.append({
                        'entity': token,
                        'category': 'COURSE_CODE',
                        'indices': [i],
                        'source': 'dynamic'
                    })
                    all_matched_indices.add(i)

        # 6. Filter bound entities and separate unmapped parameters
        final_entities = []
        unmapped_parameters = []
        for e in bound_entities:
            if e.get('source') == 'ner' and e.get('type') != 'bound_parameter':
                unmapped_parameters.append({
                    'entity': e['entity'],
                    'type': e['category'],
                    'indices': e['indices']
                })
            else:
                final_entities.append(e)

        return {
            'entities': final_entities + dynamic_course_codes,
            'unmapped_parameters': unmapped_parameters
        }

    def _validate_pos_constraints(self, category, ngram_tokens, orig_indices, pos_tags):
        """Map JSON categories to rigid POS constraints dynamically."""
        if category in self.syntactical_constraints:
            constraint = self.syntactical_constraints[category]
            
            req_word = constraint.get("required_word")
            req_pos_prefix = constraint.get("required_pos_prefix")
            invalid_pos_prefix = constraint.get("invalid_pos_prefix")
            
            if req_word and req_pos_prefix:
                for j, t in enumerate(ngram_tokens):
                    if t.lower() == req_word:
                        orig_pos = pos_tags[orig_indices[j]][1]
                        if not orig_pos.startswith(req_pos_prefix):
                            return False
                            
            if invalid_pos_prefix:
                for idx in orig_indices:
                    if pos_tags[idx][1].startswith(invalid_pos_prefix):
                        return False
                        
        return True
