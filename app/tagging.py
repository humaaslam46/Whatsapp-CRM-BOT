"""
Intent tagging for incoming lead messages.

Uses spaCy (if the 'en_core_web_sm' model is installed) to lemmatize the
message so keyword matching is more robust (e.g. "pricing", "priced",
"price" all normalize toward "price"). Falls back to plain keyword matching
if spaCy / the model isn't available, so the module still runs without it.

Swap this file for an LLM-based classifier later without touching any other
module (dedup.py, airtable_client.py, main.py don't need to change).
"""

from typing import List

_NLP = None
_SPACY_AVAILABLE = False

try:
    import spacy
    try:
        _NLP = spacy.load("en_core_web_sm")
        _SPACY_AVAILABLE = True
    except OSError:
        # Model not downloaded; run "python -m spacy download en_core_web_sm"
        _SPACY_AVAILABLE = False
except ImportError:
    _SPACY_AVAILABLE = False


INTENT_KEYWORDS = {
    "Pricing": ["price", "cost", "fee", "charge", "quote", "afford", "discount", "cheap"],
    "Demo Request": ["demo", "trial", "sample", "show me", "walkthrough"],
    "Support": ["issue", "problem", "not work", "broken", "help", "error", "complaint"],
    "Purchase Intent": ["buy", "order", "purchase", "interested", "sign up", "subscribe"],
}


def _lemmatize(text: str) -> List[str]:
    if _SPACY_AVAILABLE:
        doc = _NLP(text.lower())
        return [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
    return text.lower().split()


def tag_intent(message: str) -> str:
    """Return a single intent tag for a message. Defaults to 'General'."""
    tokens = _lemmatize(message)
    joined = " ".join(tokens)

    for tag, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in joined or kw in message.lower():
                return tag

    return "General"
