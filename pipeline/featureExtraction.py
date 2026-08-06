import json
import os
import re
import itertools

class FeatureExtractor:
    def __init__(self, json_path='academic_entities.json', binding_rules_path='binding_rules.json'):
        self.entity_dict = self._load_json(json_path)
        binding_data = self._load_json(binding_rules_path)
        self.binding_rules = binding_data.get('bindings', [])
        self.syntactical_constraints = binding_data.get('syntactical_constraints', {})
        
        # Create an inverted dictionary: lowercase n-gram phrase -> category
        self.phrase_to_category, self.max_ngram = self._build_inverted_dictionary()

    def _build_inverted_dictionary(self):
        phrase_to_category = {}
        max_ngram = 1
        for category, phrases in self.entity_dict.items():
            for phrase in phrases:
                phrase_set = frozenset(phrase.lower().split())
                phrase_to_category[phrase_set] = category
                max_ngram = max(max_ngram, len(phrase_set))
        return phrase_to_category, max_ngram

    def _load_json(self, json_path):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(current_dir, json_path)
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def extract_features(self, preprocessed_data):
        tokens = preprocessed_data['tokens']
        pos_tags = preprocessed_data['pos_tags']
        cleaned_tokens = preprocessed_data['cleaned_tokens']
        cleaned_token_indices = preprocessed_data['cleaned_token_indices']

        # 1. Dictionary Matching
        extracted_entities, matched_cleaned_indices, matched_token_indices = self._match_dictionary(
            preprocessed_data
        )

        # 2. Fallback for NNP sequences (Person names)
        self._match_nnp_fallback(tokens, pos_tags, matched_token_indices, extracted_entities)

        # Sort extracted entities by their position in the text
        extracted_entities.sort(key=lambda x: x['indices'][0])

        # 3. Parameter Binding
        bound_entities = self._bind_parameters(extracted_entities, pos_tags)

        # 4. Filter bound entities and separate unmapped parameters
        final_entities, unmapped_parameters = self._filter_and_separate_entities(bound_entities)

        return {
            'entities': final_entities,
            'unmapped_parameters': unmapped_parameters
        }

    def _is_unmapped_fallback(self, e):
        return e.get('source') == 'ner_fallback' and e.get('type') != 'bound_parameter'

    def _filter_and_separate_entities(self, bound_entities):
        final_entities = list(filter(lambda e: not self._is_unmapped_fallback(e), bound_entities))
        unmapped_parameters = [
            {'entity': e['entity'], 'type': e['category'], 'indices': e['indices']}
            for e in filter(self._is_unmapped_fallback, bound_entities)
        ]
        return final_entities, unmapped_parameters

    def _match_dictionary(self, preprocessed_data):
        extracted_entities = []
        matched_cleaned_indices = set()
        matched_token_indices = set()

        cleaned_tokens = preprocessed_data['cleaned_tokens']

        for n in range(self.max_ngram, 0, -1):
            for i in range(len(cleaned_tokens) - n + 1):
                entity = self._process_ngram(
                    n, i, preprocessed_data, matched_cleaned_indices
                )
                if entity:
                    extracted_entities.append(entity)
                    matched_cleaned_indices.update(range(i, i + n))
                    matched_token_indices.update(entity['indices'])

        return extracted_entities, matched_cleaned_indices, matched_token_indices

    def _process_ngram(self, n, i, preprocessed_data, matched_cleaned_indices):
        if not matched_cleaned_indices.isdisjoint(range(i, i + n)):
            return None

        cleaned_tokens = preprocessed_data['cleaned_tokens']
        ngram_tokens = cleaned_tokens[i:i+n]
        ngram_set = frozenset(map(str.lower, ngram_tokens))

        if len(ngram_set) != n or ngram_set not in self.phrase_to_category:
            return None

        category = self.phrase_to_category[ngram_set]
        orig_indices = preprocessed_data['cleaned_token_indices'][i:i+n]

        if self._validate_pos_constraints(category, ngram_tokens, orig_indices, preprocessed_data['pos_tags']):
            ngram_phrase = " ".join(ngram_tokens).lower()
            return {
                'entity': ngram_phrase,
                'category': category,
                'indices': orig_indices,
                'source': 'dictionary'
            }
        return None

    def _match_nnp_fallback(self, tokens, pos_tags, matched_token_indices, extracted_entities):
        nnp_indices = [i for i, (word, pos) in enumerate(pos_tags) if pos == 'NNP' and i not in matched_token_indices]

        if not nnp_indices:
            return

        groups = self._group_consecutive_indices(nnp_indices)
        for group in groups:
            entity_text = " ".join([tokens[idx] for idx in group])
            extracted_entities.append({
                'entity': entity_text,
                'category': 'PERSON',
                'indices': group,
                'source': 'ner_fallback'
            })
            matched_token_indices.update(group)

    def _group_consecutive_indices(self, indices):
        return [list(map(lambda x: x[1], g)) for k, g in itertools.groupby(enumerate(indices), lambda x: x[0] - x[1])]

    def _bind_parameters(self, extracted_entities, pos_tags):
        bound_entities = []
        i = 0
        while i < len(extracted_entities):
            curr = extracted_entities[i]
            if i + 1 < len(extracted_entities):
                nxt = extracted_entities[i+1]
                bound_entity = self._attempt_binding(curr, nxt, pos_tags)
                if bound_entity:
                    bound_entities.append(bound_entity)
                    i += 2
                    continue
            bound_entities.append(curr)
            i += 1
        return bound_entities

    def _attempt_binding(self, curr, nxt, pos_tags):
        if curr['indices'][-1] >= nxt['indices'][0]:
            return None
            
        rule = next((r for r in self.binding_rules if curr['category'] == r['action_category'] and nxt['category'] == r['target_category']), None)
        if rule:
            return {
                'action': curr['category'],
                'action_entity': curr['entity'],
                'target_category': nxt['category'],
                'target_entity': nxt['entity'],
                'indices': curr['indices'] + nxt['indices'],
                'type': 'bound_parameter'
            }
        return None

    def _validate_pos_constraints(self, category, ngram_tokens, orig_indices, pos_tags):
        """Map JSON categories to rigid POS constraints dynamically."""
        if category not in self.syntactical_constraints:
            return True
            
        constraint = self.syntactical_constraints[category]
        if not self._validate_required_pos(constraint, ngram_tokens, orig_indices, pos_tags):
            return False
            
        return self._validate_invalid_pos(constraint, orig_indices, pos_tags)

    def _validate_required_pos(self, constraint, ngram_tokens, orig_indices, pos_tags):
        req_word = constraint.get("required_word")
        req_pos_prefix = constraint.get("required_pos_prefix")
        if not (req_word and req_pos_prefix):
            return True
            
        return all(
            pos_tags[orig_indices[j]][1].startswith(req_pos_prefix)
            for j, t in enumerate(ngram_tokens)
            if t.lower() == req_word
        )

    def _validate_invalid_pos(self, constraint, orig_indices, pos_tags):
        invalid_pos_prefix = constraint.get("invalid_pos_prefix")
        if not invalid_pos_prefix:
            return True
            
        return not any(pos_tags[idx][1].startswith(invalid_pos_prefix) for idx in orig_indices)
