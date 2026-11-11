"""Resource-independent tokenization: preserve negation, numbers and offsets."""
import re

def preprocess_text(text):
    matches = list(re.finditer(r"[\w]+(?:[-'/][\w]+)*|[^\w\s]", text))
    tokens = [m.group() for m in matches]
    return dict(original_text=text, tokens=tokens,
                token_spans=[(m.start(), m.end()) for m in matches],
                pos_tags=[(t, 'NN') for t in tokens],
                lemmatized_tokens=[t.lower() for t in tokens],
                cleaned_tokens=[t.lower() for t in tokens],
                cleaned_token_indices=list(range(len(tokens))))
