import nltk
import string
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk

nltk.download('punkt_tab', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('averaged_perceptron_tagger_eng', quiet=True)
nltk.download('maxent_ne_chunker_tab', quiet=True)
nltk.download('words', quiet=True)

# Initialize the lemmatizer globally so it only loads into memory once
_lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def get_wordnet_pos(treebank_tag):
    """
    Convert Penn Treebank POS tags to WordNet POS tags.
    """
    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    else:
        return wordnet.NOUN # Default to noun

def preprocess_text(text: str) -> dict:
    """
    Step 02 Preprocessing Workflow:
    1. Tokenization
    2. POS tagging
    3. NER
    4. Lemmatization
    5. Cleaning of Digits and Punctuation (and stopwords)
    """
    # 1. Tokenization
    tokens = word_tokenize(text)
    
    # 2. POS Tagging
    pos_tags = pos_tag(tokens)
    
    # 3. NER (Named Entity Recognition)
    named_entities = ne_chunk(pos_tags)
    
    # 4. Lemmatization
    lemmatized_tokens = [
        _lemmatizer.lemmatize(token, get_wordnet_pos(tag)) 
        for token, tag in pos_tags
    ]
    
    # 5. Cleaning of Digits and Punctuation (and stopwords)
    cleaned_tokens = []
    cleaned_token_indices = []
    for i, token in enumerate(lemmatized_tokens):
        if not token.isdigit() and token not in string.punctuation and token.lower() not in stop_words:
            cleaned_tokens.append(token)
            cleaned_token_indices.append(i)
                    
    return {
        "original_text": text,
        "tokens": tokens,
        "pos_tags": pos_tags,
        "named_entities": named_entities,
        "lemmatized_tokens": lemmatized_tokens,
        "cleaned_tokens": cleaned_tokens,
        "cleaned_token_indices": cleaned_token_indices
    }
