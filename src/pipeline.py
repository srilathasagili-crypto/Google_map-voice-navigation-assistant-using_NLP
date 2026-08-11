"""
Main pipeline for NLP Voice Navigation Assistant.

Flow:
Text / Voice
      ↓
Intent Classification
      ↓
Entity Extraction
      ↓
Geocoding with Nominatim
      ↓
Driving Route with OSRM
      ↓
Route coordinates
      ↓
Streamlit Folium Map
      ↓
Response + TTS
"""

from intent_classifier import IntentClassifier
from ner_rules import extract_entities
from response_templates import generate_response

import maps_api


# ============================================================
# DEFAULT SETTINGS
# ============================================================

MOCK_MAPS = False


# ============================================================
# DEFAULT CURRENT LOCATION
# ============================================================

MOCK_CURRENT_LOCATION = {
    "lat": 17.3850,
    "lon": 78.4867,
    "display_name": "Hyderabad, India"
}


# ============================================================
# PIPELINE
# ============================================================

class VoiceAssistantPipeline:

    def __init__(self, mock_maps: bool = MOCK_MAPS):

        self.intent_classifier = IntentClassifier(
            confidence_threshold=0.35
        )

        self.mock_maps = mock_maps


    # ========================================================
    # NAVIGATION
    # ========================================================

    def handle_navigate(self, entities):

        destination = entities.get("destination")

        # ----------------------------------------------------
        # CASE 1:
        # "navigate to Charminar"
        # ----------------------------------------------------

        if not destination:
            return {
                "response": generate_response("no_result"),
                "route": None
            }


        # ----------------------------------------------------
        # CASE 2:
        # "navigate from Vijayawada to Guntur"
        # ----------------------------------------------------

        start_location = entities.get("start_location")


        # ====================================================
        # MOCK MODE
        # ====================================================

        if self.mock_maps:

            if start_location:

                return {
                    "response": (
                        f"Starting from {start_location.title()} "
                        f"and navigating to {destination.title()}."
                    ),

                    "route": {
                        "distance_km": 120.0,
                        "duration_min": 150,

                        "route_points": [],

                        "start_lat": 16.5062,
                        "start_lon": 80.6480,

                        "end_lat": 16.3067,
                        "end_lon": 80.4365,

                        "destination": destination.title()
                    }
                }

            else:

                return {
                    "response": (
                        f"Navigating to {destination.title()}."
                    ),

                    "route": {
                        "distance_km": 5.0,
                        "duration_min": 15,

                        "route_points": [],

                        "start_lat": MOCK_CURRENT_LOCATION["lat"],
                        "start_lon": MOCK_CURRENT_LOCATION["lon"],

                        "end_lat": 17.4000,
                        "end_lon": 78.4800,

                        "destination": destination.title()
                    }
                }


        # ====================================================
        # REAL MAP MODE
        # ====================================================

        # ----------------------------------------------------
        # Determine START location
        # ----------------------------------------------------

        if start_location:

            start_geo = maps_api.geocode(
                start_location
            )

        else:

            start_geo = {
                "lat": MOCK_CURRENT_LOCATION["lat"],
                "lon": MOCK_CURRENT_LOCATION["lon"],
                "display_name": MOCK_CURRENT_LOCATION["display_name"]
            }


        # ----------------------------------------------------
        # Check start location
        # ----------------------------------------------------

        if not start_geo:

            return {
                "response": (
                    f"I couldn't find the starting location "
                    f"'{start_location}'."
                ),
                "route": None
            }


        # ----------------------------------------------------
        # Geocode destination
        # ----------------------------------------------------

        destination_geo = maps_api.geocode(
            destination
        )


        if not destination_geo:

            return {
                "response": (
                    f"I couldn't find the destination "
                    f"'{destination}'. "
                    f"Could you try a more specific place name?"
                ),
                "route": None
            }


        # ----------------------------------------------------
        # Get actual driving route
        # ----------------------------------------------------

        route = maps_api.get_route(

            start_geo["lat"],
            start_geo["lon"],

            destination_geo["lat"],
            destination_geo["lon"]

        )


        if not route:

            return {
                "response": (
                    "I found the locations, but I couldn't "
                    "calculate a driving route."
                ),
                "route": None
            }


        # ----------------------------------------------------
        # Add map information
        # ----------------------------------------------------

        route["start_lat"] = start_geo["lat"]
        route["start_lon"] = start_geo["lon"]

        route["end_lat"] = destination_geo["lat"]
        route["end_lon"] = destination_geo["lon"]

        route["destination"] = destination_geo.get(
            "display_name",
            destination
        )


        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        if start_location:

            response = (
                f"Driving directions from "
                f"{start_location.title()} to "
                f"{destination.title()}. "
                f"The distance is approximately "
                f"{route['distance_km']} kilometers "
                f"and the estimated driving time is "
                f"{route['duration_min']} minutes."
            )

        else:

            response = (
                f"Driving directions to "
                f"{destination.title()}. "
                f"The distance is approximately "
                f"{route['distance_km']} kilometers "
                f"and the estimated driving time is "
                f"{route['duration_min']} minutes."
            )


        return {
            "response": response,
            "route": route
        }


    # ========================================================
    # NEARBY SEARCH
    # ========================================================

    def handle_search_nearby(self, entities):

        place_type = entities.get("place_type")

        if not place_type:

            return {
                "response": generate_response("no_result"),
                "route": None
            }


        result = maps_api.find_nearby_place(

            place_type,

            MOCK_CURRENT_LOCATION["lat"],

            MOCK_CURRENT_LOCATION["lon"]

        )


        if not result:

            return {
                "response": (
                    f"I couldn't find a nearby {place_type}."
                ),
                "route": None
            }


        response = (
            f"I found {result['display_name']} "
            f"near your location."
        )


        return {
            "response": response,
            "route": None
        }


    # ========================================================
    # TRAFFIC
    # ========================================================

    def handle_traffic_info(self, entities):

        import random

        status = random.choice([
            "light",
            "moderate",
            "heavy"
        ])

        return {
            "response": (
                f"Traffic is currently {status}."
            ),
            "route": None
        }


    # ========================================================
    # ROUTE PREFERENCE
    # ========================================================

    def handle_route_preference(self, entities):

        pref = entities.get(
            "route_preference",
            "your preferred route"
        )

        return {
            "response": (
                f"I will use the {pref.replace('_', ' ')}."
            ),
            "route": None
        }


    # ========================================================
    # CANCEL
    # ========================================================

    def handle_cancel(self, entities):

        return {
            "response": "Navigation cancelled.",
            "route": None
        }


    # ========================================================
    # CURRENT LOCATION
    # ========================================================

    def handle_current_location(self, entities):

        return {
            "response": (
                f"Your current location is "
                f"{MOCK_CURRENT_LOCATION['display_name']}."
            ),
            "route": None
        }


    # ========================================================
    # UNKNOWN
    # ========================================================

    def handle_unknown(self, entities):

        return {
            "response": (
                "Sorry, I couldn't understand "
                "your navigation request."
            ),
            "route": None
        }


    # ========================================================
    # MAIN PROCESS
    # ========================================================

    def process(self, user_text: str):

        # ----------------------------------------------------
        # Intent classification
        # ----------------------------------------------------

        intent_result = self.intent_classifier.predict(
            user_text
        )

        intent = intent_result["intent"]

        confidence = intent_result["confidence"]


        # ----------------------------------------------------
        # Entity extraction
        # ----------------------------------------------------

        entities = extract_entities(
            user_text,
            intent
        )


        # ----------------------------------------------------
        # Select handler
        # ----------------------------------------------------

        handlers = {

            "navigate":
                self.handle_navigate,

            "search_nearby":
                self.handle_search_nearby,

            "traffic_info":
                self.handle_traffic_info,

            "route_preference":
                self.handle_route_preference,

            "cancel":
                self.handle_cancel,

            "current_location":
                self.handle_current_location,

            "unknown":
                self.handle_unknown
        }


        handler = handlers.get(
            intent,
            self.handle_unknown
        )


        # ----------------------------------------------------
        # Execute handler
        # ----------------------------------------------------

        result = handler(
            entities
        )


        # ----------------------------------------------------
        # Final result
        # ----------------------------------------------------

        return {

            "input_text":
                user_text,

            "intent":
                intent,

            "confidence":
                round(
                    confidence,
                    3
                ),

            "entities":
                entities,

            "response":
                result["response"],

            "route":
                result.get("route")
        }


# ============================================================
# CLI TEST
# ============================================================

if __name__ == "__main__":

    pipeline = VoiceAssistantPipeline(
        mock_maps=False
    )

    while True:

        text = input(
            "\nEnter command: "
        )

        if text.lower() in [
            "exit",
            "quit"
        ]:

            break


        result = pipeline.process(
            text
        )


        print(
            "\nIntent:",
            result["intent"]
        )

        print(
            "Confidence:",
            result["confidence"]
        )

        print(
            "Entities:",
            result["entities"]
        )

        print(
            "Response:",
            result["response"]
        )

        print(
            "Route:",
            result["route"]
        )
