"""
Main pipeline for the NLP Voice Navigation Assistant.

Flow:

Voice/Text
    ↓
Intent Classification
    ↓
Entity Extraction
    ↓
Nominatim Geocoding
    ↓
OSRM Routing
    ↓
Response
    ↓
Streamlit Map + TTS
"""

from intent_classifier import IntentClassifier
from ner_rules import extract_entities
from response_templates import generate_response

import maps_api


# ============================================================
# MOCK CONFIGURATION
# ============================================================

MOCK_MAPS = True


MOCK_CURRENT_LOCATION = {
    "lat": 17.3850,
    "lon": 78.4867,
    "display_name": "Hyderabad, India"
}


# ============================================================
# MOCK DATA
# ============================================================

MOCK_NEARBY = {

    "hospital": {
        "display_name": "City Care Hospital",
        "distance_km": 1.4
    },

    "atm": {
        "display_name": "SBI ATM, Main Road",
        "distance_km": 0.6
    },

    "fuel_station": {
        "display_name": "HP Petrol Pump",
        "distance_km": 2.1
    },

    "pharmacy": {
        "display_name": "Apollo Pharmacy",
        "distance_km": 0.9
    },

    "restaurant": {
        "display_name": "Paradise Restaurant",
        "distance_km": 1.8
    },

    "cafe": {
        "display_name": "Cafe Coffee Day",
        "distance_km": 0.5
    },

    "bank": {
        "display_name": "HDFC Bank Branch",
        "distance_km": 1.1
    },

    "parking": {
        "display_name": "Public Parking Lot",
        "distance_km": 0.3
    },

    "grocery": {
        "display_name": "More Supermarket",
        "distance_km": 1.0
    },

    "charging_station": {
        "display_name": "Tata Power EV Charging Point",
        "distance_km": 3.0
    }
}


MOCK_DESTINATIONS = {

    "central park": {
        "distance_km": 4.2,
        "duration_min": 12
    },

    "charminar": {
        "distance_km": 6.5,
        "duration_min": 20
    },

    "hyderabad railway station": {
        "distance_km": 5.1,
        "duration_min": 15
    }
}


# ============================================================
# PIPELINE CLASS
# ============================================================

class VoiceAssistantPipeline:

    def __init__(
        self,
        mock_maps: bool = MOCK_MAPS
    ):

        self.intent_classifier = IntentClassifier(
            confidence_threshold=0.35
        )

        self.mock_maps = mock_maps


    # ========================================================
    # NAVIGATION
    # ========================================================

    def handle_navigate(
        self,
        entities
    ):

        destination = entities.get(
            "destination"
        )


        if not destination:

            return {
                "response": generate_response(
                    "no_result"
                ),
                "route": None
            }


        # ----------------------------------------------------
        # MOCK ROUTE
        # ----------------------------------------------------

        if self.mock_maps:

            route_data = MOCK_DESTINATIONS.get(

                destination.lower(),

                {
                    "distance_km": 5.0,
                    "duration_min": 15
                }
            )


            # Mock mode does not have actual road geometry

            route = {

                "distance_km":
                    route_data["distance_km"],

                "duration_min":
                    route_data["duration_min"],

                "route_points": None,

                "start_lat":
                    MOCK_CURRENT_LOCATION["lat"],

                "start_lon":
                    MOCK_CURRENT_LOCATION["lon"],

                "end_lat": None,

                "end_lon": None,

                "destination":
                    destination.title()
            }


        # ----------------------------------------------------
        # REAL MAPS
        # ----------------------------------------------------

        else:

            geo = maps_api.geocode(
                destination
            )


            if not geo:

                return {
                    "response": generate_response(
                        "no_result"
                    ),
                    "route": None
                }


            route_data = maps_api.get_route(

                MOCK_CURRENT_LOCATION["lat"],

                MOCK_CURRENT_LOCATION["lon"],

                geo["lat"],

                geo["lon"]
            )


            if not route_data:

                return {
                    "response": generate_response(
                        "no_result"
                    ),
                    "route": None
                }


            route = {

                "distance_km":
                    route_data["distance_km"],

                "duration_min":
                    route_data["duration_min"],

                "route_points":
                    route_data.get(
                        "route_points"
                    ),

                "start_lat":
                    MOCK_CURRENT_LOCATION["lat"],

                "start_lon":
                    MOCK_CURRENT_LOCATION["lon"],

                "end_lat":
                    geo["lat"],

                "end_lon":
                    geo["lon"],

                "destination":
                    destination.title()
            }


        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        response = generate_response(

            "navigate",

            {

                "destination":
                    destination.title(),

                "distance_km":
                    route["distance_km"],

                "duration_min":
                    route["duration_min"]
            }
        )


        return {

            "response": response,

            "route": route
        }


    # ========================================================
    # SEARCH NEARBY
    # ========================================================

    def handle_search_nearby(
        self,
        entities
    ):

        place_type = entities.get(
            "place_type"
        )


        if not place_type:

            return {
                "response": generate_response(
                    "no_result"
                ),
                "route": None
            }


        # ----------------------------------------------------
        # MOCK
        # ----------------------------------------------------

        if self.mock_maps:

            place = MOCK_NEARBY.get(
                place_type
            )


        # ----------------------------------------------------
        # REAL MAPS
        # ----------------------------------------------------

        else:

            result = maps_api.find_nearby_place(

                place_type,

                MOCK_CURRENT_LOCATION["lat"],

                MOCK_CURRENT_LOCATION["lon"]
            )


            if result:

                place = {

                    "display_name":
                        result["display_name"],

                    "distance_km":
                        1.0
                }

            else:

                place = None


        if not place:

            return {

                "response":
                    generate_response(
                        "no_result"
                    ),

                "route": None
            }


        response = generate_response(

            "search_nearby",

            {

                "place_type":
                    place_type.replace(
                        "_",
                        " "
                    ),

                "place_name":
                    place["display_name"],

                "distance_km":
                    place["distance_km"]
            }
        )


        return {

            "response": response,

            "route": None
        }


    # ========================================================
    # TRAFFIC
    # ========================================================

    def handle_traffic_info(
        self,
        entities
    ):

        import random

        status = random.choice(

            [
                "light",
                "moderate",
                "heavy"
            ]
        )


        return {

            "response":
                generate_response(

                    "traffic_info",

                    {
                        "traffic_status":
                            status
                    }
                ),

            "route": None
        }


    # ========================================================
    # ROUTE PREFERENCE
    # ========================================================

    def handle_route_preference(
        self,
        entities
    ):

        preference = entities.get(

            "route_preference",

            "your preferred route"
        )


        return {

            "response":
                generate_response(

                    "route_preference",

                    {

                        "preference":
                            preference.replace(
                                "_",
                                " "
                            )
                    }
                ),

            "route": None
        }


    # ========================================================
    # CANCEL
    # ========================================================

    def handle_cancel(
        self,
        entities
    ):

        return {

            "response":
                generate_response(
                    "cancel"
                ),

            "route": None
        }


    # ========================================================
    # CURRENT LOCATION
    # ========================================================

    def handle_current_location(
        self,
        entities
    ):

        return {

            "response":
                generate_response(

                    "current_location",

                    {

                        "place_name":
                            MOCK_CURRENT_LOCATION[
                                "display_name"
                            ]
                    }
                ),

            "route": None
        }


    # ========================================================
    # UNKNOWN
    # ========================================================

    def handle_unknown(
        self,
        entities
    ):

        return {

            "response":
                generate_response(
                    "unknown"
                ),

            "route": None
        }


    # ========================================================
    # MAIN PROCESS
    # ========================================================

    def process(
        self,
        user_text: str
    ):

        # ----------------------------------------------------
        # INTENT
        # ----------------------------------------------------

        intent_result = (
            self.intent_classifier.predict(
                user_text
            )
        )


        intent = intent_result[
            "intent"
        ]


        confidence = intent_result[
            "confidence"
        ]


        # ----------------------------------------------------
        # ENTITY EXTRACTION
        # ----------------------------------------------------

        entities = extract_entities(

            user_text,

            intent
        )


        # ----------------------------------------------------
        # HANDLERS
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
        # EXECUTE HANDLER
        # ----------------------------------------------------

        handler_result = handler(
            entities
        )


        # ----------------------------------------------------
        # FINAL RESULT
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
                handler_result[
                    "response"
                ],

            "route":
                handler_result.get(
                    "route"
                )
        }


# ============================================================
# CLI
# ============================================================

def run_cli(
    use_microphone: bool = False
):

    from speech_io import listen, speak

    pipeline = VoiceAssistantPipeline()


    print(
        "=" * 60
    )

    print(
        "NLP Voice Assistant"
    )

    print(
        "Type 'quit' to exit."
    )

    print(
        "=" * 60
    )


    while True:

        user_text = listen(
            use_microphone=
                use_microphone
        )


        if user_text.strip().lower() in (
            "quit",
            "exit"
        ):

            print(
                "Goodbye!"
            )

            break


        result = pipeline.process(
            user_text
        )


        print(
            f"Intent: "
            f"{result['intent']}"
        )


        print(
            f"Confidence: "
            f"{result['confidence']}"
        )


        print(
            f"Entities: "
            f"{result['entities']}"
        )


        print(
            result["response"]
        )


        speak(
            result["response"],
            use_audio=False
        )


        print(
            "-" * 60
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    run_cli(
        use_microphone=False
    )
