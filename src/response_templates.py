"""
Template-based response generation.
No LLM — responses are built from predefined templates filled with
slot values extracted from intent + entities + maps API results.
"""

import random

TEMPLATES = {
    "navigate": [
        "Starting navigation to {destination}. It's {distance_km} km away, about {duration_min} minutes.",
        "Heading to {destination} now. Estimated distance is {distance_km} km, {duration_min} minutes away.",
        "Route to {destination} found: {distance_km} km, roughly {duration_min} minutes.",
    ],
    "search_nearby": [
        "The nearest {place_type} is {place_name}, about {distance_km} km from you.",
        "Found a {place_type} nearby: {place_name}, {distance_km} km away.",
    ],
    "traffic_info": [
        "Current traffic on your route looks {traffic_status}.",
        "Traffic update: conditions are {traffic_status} right now.",
    ],
    "route_preference": [
        "Got it, I'll adjust the route to {preference}.",
        "Updating your route preference to {preference}.",
    ],
    "cancel": [
        "Navigation cancelled.",
        "Trip ended. Let me know if you need directions again.",
    ],
    "current_location": [
        "You are currently near {place_name}.",
        "Your current location is close to {place_name}.",
    ],
    "unknown": [
        "Sorry, I didn't quite catch that. Could you rephrase your request?",
        "I'm not confident I understood. Could you say that differently?",
    ],
    "no_result": [
        "I couldn't find that location. Could you try a more specific place name?",
    ],
}


def generate_response(intent: str, slots: dict = None) -> str:
    slots = slots or {}
    options = TEMPLATES.get(intent, TEMPLATES["unknown"])
    template = random.choice(options)
    try:
        return template.format(**slots)
    except KeyError:
        # Missing slot data (e.g., maps API returned nothing) — fall back safely
        return random.choice(TEMPLATES["no_result"])


if __name__ == "__main__":
    print(generate_response("navigate", {"destination": "Central Park", "distance_km": 4.2, "duration_min": 12}))
    print(generate_response("search_nearby", {"place_type": "hospital", "place_name": "City Hospital", "distance_km": 1.3}))
    print(generate_response("unknown"))
