"""
Text preprocessing module for the NLP voice assistant pipeline.
Handles: lowercasing, tokenization, stopword removal, lemmatization.
"""

import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# Download required NLTK data (only runs once)
for resource in ["punkt", "punkt_tab", "stopwords", "wordnet", "omw-1.4"]:
    try:
        nltk.data.find(f"tokenizers/{resource}") if "punkt" in resource else nltk.data.find(f"corpora/{resource}")
    except LookupError:
        nltk.download(resource, quiet=True)

_lemmatizer = WordNetLemmatizer()
_stop_words = set(stopwords.words("english"))

# Keep words that matter for intent/entity meaning even though they're
# technically "stopwords" (e.g., negations, prepositions used in navigation context)
_KEEP_WORDS = {"near", "nearby", "to", "at", "from", "no", "not", "without"}
_stop_words = _stop_words - _KEEP_WORDS


def clean_text(text: str) -> str:
    """Lowercase and strip non-alphanumeric noise while keeping spaces."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text: str) -> list:
    return word_tokenize(text)


def remove_stopwords(tokens: list) -> list:
    return [t for t in tokens if t not in _stop_words]


def lemmatize(tokens: list) -> list:
    return [_lemmatizer.lemmatize(t) for t in tokens]


def preprocess(text: str, keep_stopwords: bool = False) -> str:
    """
    Full preprocessing pipeline used before TF-IDF vectorization.
    keep_stopwords=True is useful for the NER stage, since entity
    words like "near" or "to" carry meaning there.
    """
    text = clean_text(text)
    tokens = tokenize(text)
    if not keep_stopwords:
        tokens = remove_stopwords(tokens)
    tokens = lemmatize(tokens)
    return " ".join(tokens)


if __name__ == "__main__":
    sample = "Navigate me to the nearest ATM near Hyderabad station!"
    print("Original:", sample)
    print("Preprocessed:", preprocess(sample))
