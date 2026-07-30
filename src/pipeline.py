"""
Main pipeline: orchestrates STT -> Intent Classification -> NER ->
Maps API -> Response Template -> TTS.

Includes a MOCK_MAPS fallback: if the live Nominatim/OSRM APIs are
unreachable (e.g. rate-limited, no internet, or blocked network like in
a sandboxed dev environment), the pipeline uses realistic mock data so
the full NLP flow can still be demoed end-to-end.
"""

from intent_classifier import IntentClassifier
from ner_rules import extract_entities
from response_templates import generate_response
from speech_io import listen, speak
import maps_api

MOCK_MAPS = True  # set to False when running with real internet access

# A simple mock "current location" for demo purposes
MOCK_CURRENT_LOCATION = {"lat": 17.3850, "lon": 78.4867, "display_name": "Hyderabad, India"}

MOCK_NEARBY = {
    "hospital": {"display_name": "City Care Hospital", "distance_km": 1.4},
    "atm": {"display_name": "SBI ATM, Main Road", "distance_km": 0.6},
    "fuel_station": {"display_name": "HP Petrol Pump", "distance_km": 2.1},
    "pharmacy": {"display_name": "Apollo Pharmacy", "distance_km": 0.9},
    "restaurant": {"display_name": "Paradise Restaurant", "distance_km": 1.8},
    "cafe": {"display_name": "Cafe Coffee Day", "distance_km": 0.5},
    "bank": {"display_name": "HDFC Bank Branch", "distance_km": 1.1},
    "parking": {"display_name": "Public Parking Lot", "distance_km": 0.3},
    "grocery": {"display_name": "More Supermarket", "distance_km": 1.0},
    "charging_station": {"display_name": "Tata Power EV Charging Point", "distance_km": 3.0},
}

MOCK_DESTINATIONS = {
    "central park": {"distance_km": 4.2, "duration_min": 12},
    "charminar": {"distance_km": 6.5, "duration_min": 20},
    "hyderabad railway station": {"distance_km": 5.1, "duration_min": 15},
}


class VoiceAssistantPipeline:
    def __init__(self, mock_maps: bool = MOCK_MAPS):
        self.intent_classifier = IntentClassifier(confidence_threshold=0.35)
        self.mock_maps = mock_maps

    def handle_navigate(self, entities):
        destination = entities.get("destination")
        if not destination:
            return generate_response("no_result")

        if self.mock_maps:
            route = MOCK_DESTINATIONS.get(
                destination, {"distance_km": 5.0, "duration_min": 15}
            )
        else:
            geo = maps_api.geocode(destination)
            if not geo:
                return generate_response("no_result")
            route = maps_api.get_route(
                MOCK_CURRENT_LOCATION["lat"], MOCK_CURRENT_LOCATION["lon"],
                geo["lat"], geo["lon"]
            )
            if not route:
                return generate_response("no_result")

        return generate_response("navigate", {
            "destination": destination.title(),
            "distance_km": route["distance_km"],
            "duration_min": route["duration_min"],
        })

    def handle_search_nearby(self, entities):
        place_type = entities.get("place_type")
        if not place_type:
            return generate_response("no_result")

        if self.mock_maps:
            place = MOCK_NEARBY.get(place_type)
        else:
            result = maps_api.find_nearby_place(
                place_type, MOCK_CURRENT_LOCATION["lat"], MOCK_CURRENT_LOCATION["lon"]
            )
            place = {"display_name": result["display_name"], "distance_km": 1.0} if result else None

        if not place:
            return generate_response("no_result")

        return generate_response("search_nearby", {
            "place_type": place_type.replace("_", " "),
            "place_name": place["display_name"],
            "distance_km": place["distance_km"],
        })

    def handle_traffic_info(self, entities):
        # Mocked traffic status — a real system would call a live traffic API
        import random
        status = random.choice(["light", "moderate", "heavy"])
        return generate_response("traffic_info", {"traffic_status": status})

    def handle_route_preference(self, entities):
        pref = entities.get("route_preference", "your preferred route")
        return generate_response("route_preference", {"preference": pref.replace("_", " ")})

    def handle_cancel(self, entities):
        return generate_response("cancel")

    def handle_current_location(self, entities):
        return generate_response("current_location", {
            "place_name": MOCK_CURRENT_LOCATION["display_name"]
        })

    def handle_unknown(self, entities):
        return generate_response("unknown")

    def process(self, user_text: str) -> dict:
        """Runs the full pipeline on a single text input and returns the result."""
        intent_result = self.intent_classifier.predict(user_text)
        intent = intent_result["intent"]
        confidence = intent_result["confidence"]

        entities = extract_entities(user_text, intent)

        handlers = {
            "navigate": self.handle_navigate,
            "search_nearby": self.handle_search_nearby,
            "traffic_info": self.handle_traffic_info,
            "route_preference": self.handle_route_preference,
            "cancel": self.handle_cancel,
            "current_location": self.handle_current_location,
            "unknown": self.handle_unknown,
        }

        handler = handlers.get(intent, self.handle_unknown)
        response_text = handler(entities)

        return {
            "input_text": user_text,
            "intent": intent,
            "confidence": round(confidence, 3),
            "entities": entities,
            "response": response_text,
        }


def run_cli(use_microphone: bool = False):
    """Interactive CLI loop — text mode by default for this sandbox."""
    pipeline = VoiceAssistantPipeline()
    print("=" * 60)
    print("NLP Voice Assistant (Google Maps style, no LLM)")
    print("Type 'quit' to exit.")
    print("=" * 60)

    while True:
        user_text = listen(use_microphone=use_microphone)
        if user_text.strip().lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        result = pipeline.process(user_text)
        print(f"  Intent: {result['intent']} (confidence: {result['confidence']})")
        print(f"  Entities: {result['entities']}")
        speak(result["response"], use_audio=False)
        print("-" * 60)


if __name__ == "__main__":
    run_cli(use_microphone=False)
