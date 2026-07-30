"""
Rule-based Named Entity Recognition for the navigation domain.

Why rule-based instead of spaCy's statistical NER:
spaCy's pretrained NER is trained on general news/web text and recognizes
generic categories (PERSON, GPE, ORG). Our domain has a small, closed set
of entity types (place-type, destination, route-preference) that are far
more reliably extracted with gazetteers + regex patterns than by a
general-purpose statistical model that has never seen "nearest ATM" as
a training example in this context.
"""

import re
from preprocess import clean_text

# Gazetteer of known "place type" queries (search_nearby intent)
PLACE_TYPES = {
    "hospital": ["hospital", "hospitals", "clinic", "clinics"],
    "atm": ["atm", "atms", "cash machine"],
    "fuel_station": ["petrol pump", "gas station", "fuel station", "petrol station"],
    "pharmacy": ["pharmacy", "pharmacies", "medical store", "chemist"],
    "restaurant": ["restaurant", "restaurants", "eatery", "food court"],
    "cafe": ["coffee shop", "cafe", "cafes"],
    "bank": ["bank", "banks"],
    "parking": ["parking", "parking lot"],
    "grocery": ["grocery store", "supermarket", "grocery"],
    "charging_station": ["charging station", "ev charging", "charging point"],
}

# Route preference keywords
ROUTE_PREFERENCES = {
    "avoid_highway": ["avoid highway", "avoid highways", "no highway"],
    "avoid_tolls": ["avoid toll", "avoid tolls", "no toll"],
    "fastest": ["fastest route", "quickest way", "quickest route"],
    "shortest": ["shortest path", "shortest route"],
    "scenic": ["scenic route"],
    "no_traffic": ["without traffic", "avoid traffic", "no traffic"],
    "walking": ["walking directions", "prefer walking", "on foot"],
    "public_transport": ["public transport", "bus route", "train route"],
}

# Words to strip out when trying to isolate a destination name
_FILLER_PATTERNS = [
    r"\b(navigate|route|directions?|guide|show|take|plot)\b",
    r"\b(me|to|the|for|please|towards?)\b",
    r"\b(i want to go|i need|how do i get|find (a|the)?|way to)\b",
]


def extract_place_type(text: str):
    text = text.lower()
    for canonical, variants in PLACE_TYPES.items():
        for v in variants:
            if v in text:
                return canonical
    return None


def extract_route_preference(text: str):
    text = text.lower()
    for canonical, variants in ROUTE_PREFERENCES.items():
        for v in variants:
            if v in text:
                return canonical
    return None


def extract_destination(text: str):
    """
    Heuristic destination extraction: strip known filler/command words
    and return what's left as the likely destination phrase.
    Works for navigate-intent queries like "navigate to central park".
    """
    text = text.lower().strip()
    for pattern in _FILLER_PATTERNS:
        text = re.sub(pattern, "", text)
    text = re.sub(r"\s+", " ", text).strip(" .,!?")
    return text if text else None


def extract_entities(text: str, intent: str = None):
    """
    Main entity extraction function — returns a dict of entities found,
    tailored based on the predicted intent (if provided) to reduce
    false positives (e.g., don't try to extract a destination for a
    traffic_info query).
    """
    entities = {}

    place_type = extract_place_type(text)
    if place_type:
        entities["place_type"] = place_type

    route_pref = extract_route_preference(text)
    if route_pref:
        entities["route_preference"] = route_pref

    if intent == "navigate" or (intent is None and not place_type):
        destination = extract_destination(text)
        if destination:
            entities["destination"] = destination

    return entities


if __name__ == "__main__":
    tests = [
        ("navigate to central park", "navigate"),
        ("find nearest hospital", "search_nearby"),
        ("avoid tolls please", "route_preference"),
        ("take me to hyderabad railway station", "navigate"),
    ]
    for text, intent in tests:
        print(f"'{text}' -> {extract_entities(text, intent)}")
