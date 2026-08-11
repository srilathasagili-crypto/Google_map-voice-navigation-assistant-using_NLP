"""
Rule-based Named Entity Recognition for the navigation domain.

Supports:
- Single destination:
    navigate to Charminar

- Origin + destination:
    navigate from Vijayawada to Guntur
    directions from Hyderabad to Warangal
    go from Secunderabad to Charminar

- Nearby places:
    find nearest hospital
    find nearest ATM

- Route preferences:
    avoid tolls
    fastest route
"""

import re

from preprocess import clean_text


# ============================================================
# PLACE TYPES
# ============================================================

PLACE_TYPES = {
    "hospital": [
        "hospital",
        "hospitals",
        "clinic",
        "clinics"
    ],

    "atm": [
        "atm",
        "atms",
        "cash machine"
    ],

    "fuel_station": [
        "petrol pump",
        "gas station",
        "fuel station",
        "petrol station"
    ],

    "pharmacy": [
        "pharmacy",
        "pharmacies",
        "medical store",
        "chemist"
    ],

    "restaurant": [
        "restaurant",
        "restaurants",
        "eatery",
        "food court"
    ],

    "cafe": [
        "coffee shop",
        "cafe",
        "cafes"
    ],

    "bank": [
        "bank",
        "banks"
    ],

    "parking": [
        "parking",
        "parking lot"
    ],

    "grocery": [
        "grocery store",
        "supermarket",
        "grocery"
    ],

    "charging_station": [
        "charging station",
        "ev charging",
        "charging point"
    ],
}


# ============================================================
# ROUTE PREFERENCES
# ============================================================

ROUTE_PREFERENCES = {
    "avoid_highway": [
        "avoid highway",
        "avoid highways",
        "no highway"
    ],

    "avoid_tolls": [
        "avoid toll",
        "avoid tolls",
        "no toll"
    ],

    "fastest": [
        "fastest route",
        "quickest way",
        "quickest route"
    ],

    "shortest": [
        "shortest path",
        "shortest route"
    ],

    "scenic": [
        "scenic route"
    ],

    "no_traffic": [
        "without traffic",
        "avoid traffic",
        "no traffic"
    ],

    "walking": [
        "walking directions",
        "prefer walking",
        "on foot"
    ],

    "public_transport": [
        "public transport",
        "bus route",
        "train route"
    ],
}


# ============================================================
# PLACE TYPE EXTRACTION
# ============================================================

def extract_place_type(text: str):

    text = text.lower()

    for canonical, variants in PLACE_TYPES.items():

        for variant in variants:

            if variant in text:
                return canonical

    return None


# ============================================================
# ROUTE PREFERENCE EXTRACTION
# ============================================================

def extract_route_preference(text: str):

    text = text.lower()

    for canonical, variants in ROUTE_PREFERENCES.items():

        for variant in variants:

            if variant in text:
                return canonical

    return None


# ============================================================
# ORIGIN + DESTINATION EXTRACTION
# ============================================================

def extract_origin_destination(text: str):
    """
    Extract origin and destination from commands such as:

        navigate from Vijayawada to Guntur

        directions from Hyderabad to Warangal

        go from Secunderabad to Charminar

        route from Kukatpally to Gachibowli
    """

    text = text.lower().strip()

    # Remove punctuation
    text = re.sub(
        r"[.,!?]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()


    # --------------------------------------------------------
    # Pattern 1:
    #
    # from X to Y
    # --------------------------------------------------------

    pattern = r"\bfrom\s+(.+?)\s+to\s+(.+)$"

    match = re.search(
        pattern,
        text
    )


    if match:

        origin = match.group(1).strip()

        destination = match.group(2).strip()


        # Remove common ending words
        destination = re.sub(
            r"\bplease\b$",
            "",
            destination
        ).strip()


        if origin and destination:

            return {
                "origin": origin,
                "destination": destination
            }


    # --------------------------------------------------------
    # Pattern 2:
    #
    # X to Y
    #
    # Used for phrases like:
    # Vijayawada to Guntur
    # Hyderabad to Warangal
    # --------------------------------------------------------

    pattern = r"^(.+?)\s+to\s+(.+)$"

    match = re.search(
        pattern,
        text
    )


    if match:

        origin = match.group(1).strip()

        destination = match.group(2).strip()


        # Remove navigation words from origin
        origin = re.sub(
            r"^(navigate|route|directions?|go|travel)\s+",
            "",
            origin
        ).strip()


        if origin and destination:

            return {
                "origin": origin,
                "destination": destination
            }


    return None


# ============================================================
# SINGLE DESTINATION EXTRACTION
# ============================================================

def extract_destination(text: str):

    text = text.lower().strip()


    # --------------------------------------------------------
    # First check whether this is:
    #
    # from A to B
    #
    # If yes, don't treat the entire phrase as destination.
    # --------------------------------------------------------

    route = extract_origin_destination(text)

    if route:

        return route["destination"]


    # --------------------------------------------------------
    # Filler words
    # --------------------------------------------------------

    filler_patterns = [

        r"\b(navigate|route|directions?|guide|show|take|plot)\b",

        r"\b(me|to|the|for|please|towards?)\b",

        r"\b(i want to go|i need|how do i get|find (a|the)?|way to)\b",
    ]


    for pattern in filler_patterns:

        text = re.sub(
            pattern,
            "",
            text
        )


    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip(
        " .,?!"
    )


    return text if text else None


# ============================================================
# MAIN ENTITY EXTRACTION
# ============================================================

def extract_entities(
    text: str,
    intent: str = None
):

    entities = {}


    # --------------------------------------------------------
    # PLACE TYPE
    # --------------------------------------------------------

    place_type = extract_place_type(
        text
    )

    if place_type:

        entities["place_type"] = place_type


    # --------------------------------------------------------
    # ROUTE PREFERENCE
    # --------------------------------------------------------

    route_pref = extract_route_preference(
        text
    )

    if route_pref:

        entities["route_preference"] = route_pref


    # --------------------------------------------------------
    # NAVIGATION
    # --------------------------------------------------------

    if intent == "navigate" or (
        intent is None and not place_type
    ):

        # First check for:
        # origin + destination

        route = extract_origin_destination(
            text
        )


        if route:

            entities["origin"] = route[
                "origin"
            ]

            entities["destination"] = route[
                "destination"
            ]


        else:

            # Otherwise extract
            # only destination

            destination = extract_destination(
                text
            )


            if destination:

                entities["destination"] = (
                    destination
                )


    return entities


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    tests = [

        (
            "navigate to central park",
            "navigate"
        ),

        (
            "find nearest hospital",
            "search_nearby"
        ),

        (
            "avoid tolls please",
            "route_preference"
        ),

        (
            "take me to hyderabad railway station",
            "navigate"
        ),

        (
            "navigate from Vijayawada to Guntur",
            "navigate"
        ),

        (
            "directions from Hyderabad to Warangal",
            "navigate"
        ),

        (
            "go from Secunderabad to Charminar",
            "navigate"
        ),

        (
            "route from Kukatpally to Gachibowli",
            "navigate"
        ),
    ]


    for text, intent in tests:

        print(
            f"\n{text}"
        )

        print(
            extract_entities(
                text,
                intent
            )
        )
