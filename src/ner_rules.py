"""
Rule-based Named Entity Recognition for NLP Voice Navigation Assistant.

Extracts:
- start_location
- destination
- place_type
- route_preference

Examples:

navigate to Charminar
    -> destination = charminar

navigate from Vijayawada to Guntur
    -> start_location = vijayawada
    -> destination = guntur

take me from Hyderabad to Secunderabad
    -> start_location = hyderabad
    -> destination = secunderabad

find nearest hospital
    -> place_type = hospital
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
    ]
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
    ]
}


# ============================================================
# FILLER WORDS
# ============================================================

_FILLER_PATTERNS = [

    r"\b(navigate|navigation|route|routes|direction|directions)\b",

    r"\b(show|give|take|guide)\b",

    r"\b(me|please|the|a|an)\b",

    r"\b(i want to go|i need to go|i want to travel)\b",

    r"\b(how do i get)\b",

    r"\b(way to)\b"
]


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
# CLEAN DESTINATION
# ============================================================

def clean_location(location: str):

    """
    Clean a location extracted from the command.
    """

    location = location.lower().strip()

    # Remove punctuation

    location = re.sub(
        r"[,.!?]+",
        " ",
        location
    )

    # Remove extra spaces

    location = re.sub(
        r"\s+",
        " ",
        location
    ).strip()

    # Remove common filler words

    for pattern in _FILLER_PATTERNS:

        location = re.sub(
            pattern,
            "",
            location,
            flags=re.IGNORECASE
        )

    location = re.sub(
        r"\s+",
        " ",
        location
    ).strip()

    return location


# ============================================================
# EXTRACT START + DESTINATION
# ============================================================

def extract_from_to(text: str):

    """
    Extract:

        from A to B

    Example:

        Navigate from Vijayawada to Guntur

    Returns:

        {
            "start_location": "vijayawada",
            "destination": "guntur"
        }
    """

    text = text.lower().strip()


    # --------------------------------------------------------
    # Pattern:
    #
    # from A to B
    # --------------------------------------------------------

    pattern = r"\bfrom\s+(.+?)\s+to\s+(.+)$"

    match = re.search(
        pattern,
        text
    )


    if not match:

        return None


    start_location = match.group(
        1
    ).strip()


    destination = match.group(
        2
    ).strip()


    start_location = clean_location(
        start_location
    )


    destination = clean_location(
        destination
    )


    if not start_location or not destination:

        return None


    return {

        "start_location":
            start_location,

        "destination":
            destination
    }


# ============================================================
# EXTRACT "TO DESTINATION"
# ============================================================

def extract_to_destination(text: str):

    """
    Extract destination from:

        navigate to Charminar

        take me to Guntur

        go to Hyderabad
    """

    text = text.lower().strip()


    # --------------------------------------------------------
    # Pattern:
    #
    # to destination
    # --------------------------------------------------------

    pattern = r"\bto\s+(.+)$"

    match = re.search(
        pattern,
        text
    )


    if not match:

        return None


    destination = match.group(
        1
    ).strip()


    destination = clean_location(
        destination
    )


    return destination if destination else None


# ============================================================
# EXTRACT DESTINATION
# ============================================================

def extract_destination(text: str):

    """
    Extract destination for simple navigation commands.
    """

    text = text.lower().strip()


    # --------------------------------------------------------
    # First check FROM -> TO
    # --------------------------------------------------------

    from_to = extract_from_to(
        text
    )


    if from_to:

        return from_to["destination"]


    # --------------------------------------------------------
    # Otherwise check TO
    # --------------------------------------------------------

    destination = extract_to_destination(
        text
    )


    if destination:

        return destination


    return None


# ============================================================
# MAIN ENTITY EXTRACTION
# ============================================================

def extract_entities(
    text: str,
    intent: str = None
):

    """
    Main entity extraction function.
    """

    entities = {}


    # ========================================================
    # PLACE TYPE
    # ========================================================

    place_type = extract_place_type(
        text
    )


    if place_type:

        entities["place_type"] = place_type


    # ========================================================
    # ROUTE PREFERENCE
    # ========================================================

    route_pref = extract_route_preference(
        text
    )


    if route_pref:

        entities["route_preference"] = route_pref


    # ========================================================
    # NAVIGATION
    # ========================================================

    if intent == "navigate":

        # ----------------------------------------------------
        # Try "from A to B"
        # ----------------------------------------------------

        from_to = extract_from_to(
            text
        )


        if from_to:

            entities["start_location"] = (
                from_to["start_location"]
            )

            entities["destination"] = (
                from_to["destination"]
            )


        else:

            # ------------------------------------------------
            # Simple "to B"
            # ------------------------------------------------

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
            "take me from Hyderabad to Secunderabad",
            "navigate"
        ),

        (
            "give directions from Chennai to Bangalore",
            "navigate"
        )
    ]


    for text, intent in tests:

        print(
            "\nInput:",
            text
        )

        print(
            "Entities:",
            extract_entities(
                text,
                intent
            )
        )
