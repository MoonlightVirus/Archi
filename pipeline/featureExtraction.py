import json
import os
import re
from nltk.tree import Tree

class FeatureExtractor:
    def __init__(self, json_path='academic_entities.json'):
        self.entity_dict = self._load_entities(json_path)
        # Create an inverted dictionary: lowercase n-gram phrase -> category
        self.phrase_to_category = {}
        for category, phrases in self.entity_dict.items():
            for phrase in phrases:
                self.phrase_to_category[phrase.lower()] = category

    def _load_entities(self, json_path):
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

        # Construct N in {4, 3, 2, 1} overlapping sequences
        for n in [4, 3, 2, 1]:
            for i in range(len(cleaned_tokens) - n + 1):
                # Prevent sub-phrases from matching if a longer n-gram already matched
                if any((i + j) in matched_cleaned_indices for j in range(n)):
                    continue
                
                ngram_tokens = cleaned_tokens[i:i+n]
                ngram_phrase = " ".join(ngram_tokens).lower()
                
                if ngram_phrase in self.phrase_to_category:
                    category = self.phrase_to_category[ngram_phrase]
                    orig_indices = [cleaned_token_indices[i+j] for j in range(n)]
                    
                    # 3. Syntactical Disambiguation: Keyword Overlap
                    if self._validate_pos_constraints(category, ngram_tokens, orig_indices, pos_tags):
                        extracted_entities.append({
                            'entity': ngram_phrase,
                            'category': category,
                            'indices': orig_indices,
                            'source': 'dictionary'
                        })
                        for j in range(n):
                            matched_cleaned_indices.add(i + j)

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
                
                if curr['category'] == 'ACTION_CANCEL' and nxt['category'] == 'COURSE_CODE':
                    # Ensure proximity
                    if curr['indices'][-1] < nxt['indices'][0]:
                        curr_pos = pos_tags[curr['indices'][-1]][1]
                        nxt_pos = pos_tags[nxt['indices'][0]][1]
                        
                        # ACTION_CANCEL must be Verb, COURSE_CODE must be Noun
                        if curr_pos.startswith('V') and nxt_pos.startswith('N'):
                            bound_entities.append({
                                'action': curr['category'],
                                'action_entity': curr['entity'],
                                'target_category': nxt['category'],
                                'target_entity': nxt['entity'],
                                'indices': curr['indices'] + nxt['indices'],
                                'type': 'bound_parameter'
                            })
                            skip_next = True
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
                    # 'category' key is only present in single entities, not bound_parameter dicts
                    cat = e.get('category')
                    if cat in ['ENROLLMENT_TERM', 'GRADING_TERM']:
                        dist = min(abs(i - idx) for idx in e['indices'])
                        if dist <= 3:  # Define adjacency window
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

        # 6. Unstructured Entity Routing
        unmapped_parameters = []
            
        current_token_idx = 0
        for chunk in named_entities:
            if isinstance(chunk, Tree):
                label = chunk.label()
                chunk_leaves = chunk.leaves()
                chunk_len = len(chunk_leaves)
                
                # Out-of-Vocabulary (OOV): Intercept ORGANIZATION or PERSON
                if label in ['PERSON', 'ORGANIZATION']:
                    is_matched = any((current_token_idx + j) in all_matched_indices for j in range(chunk_len))
                    if not is_matched:
                        entity_text = " ".join([leaf[0] for leaf in chunk_leaves])
                        unmapped_parameters.append({
                            'entity': entity_text,
                            'type': label,
                            'indices': list(range(current_token_idx, current_token_idx + chunk_len))
                        })
                current_token_idx += chunk_len
            else:
                current_token_idx += 1

                    
        return {
            'entities': bound_entities + dynamic_course_codes,
            'unmapped_parameters': unmapped_parameters
        }

    def _validate_pos_constraints(self, category, ngram_tokens, orig_indices, pos_tags):
        """Map JSON categories to rigid POS constraints."""
        if category == 'RETENTION_TERM':
            # The unigram "shift" must carry a verb tag (VB, VBP)
            for j, t in enumerate(ngram_tokens):
                if t.lower() == 'shift':
                    orig_pos = pos_tags[orig_indices[j]][1]
                    if not orig_pos.startswith('V'):
                        return False
                        
        elif category == 'ACTION_CANCEL':
            # Action verbs should carry a verb tag
            for idx in orig_indices:
                if pos_tags[idx][1].startswith('N'):
                    return False
        
        return True
