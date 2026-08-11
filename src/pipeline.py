"""
Main pipeline: orchestrates

STT / Text
    ↓
Intent Classification
    ↓
NER / Entity Extraction
    ↓
Maps API
    ↓
Response Template
    ↓
TTS

Navigation now also returns:
    - Start location
    - Destination location
    - Distance
    - Duration
    - Actual OSRM route coordinates

These route coordinates can be used by Streamlit + Folium
to display the actual driving route on a map.

MOCK_MAPS:
    True  -> Uses mock map data
    False -> Uses real Nominatim + OSRM APIs
"""

from intent_classifier import IntentClassifier
from ner_rules import extract_entities
from response_templates import generate_response
from speech_io import listen, speak
import maps_api

MOCK_MAPS = True

MOCK_CURRENT_LOCATION = {
    "lat": 17.3850,
    "lon": 78.4867,
    "display_name": "Hyderabad, India"
}

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


# Used only when MOCK_MAPS = True.

MOCK_DESTINATIONS = {

    "central park": {
        "distance_km": 4.2,
        "duration_min": 12,
        "route_points": None
    },

    "charminar": {
        "distance_km": 6.5,
        "duration_min": 20,
        "route_points": None
    },

    "hyderabad railway station": {
        "distance_km": 5.1,
        "duration_min": 15,
        "route_points": None
    }
}

class VoiceAssistantPipeline:

    def __init__(
        self,
        mock_maps: bool = MOCK_MAPS
    ):

        # Intent classifier
        self.intent_classifier = IntentClassifier(
            confidence_threshold=0.35
        )

        # Store map mode
        self.mock_maps = mock_maps


    def handle_navigate(self, entities):

        # Get destination extracted by NER
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


        # Variable used for destination coordinates
        geo = None

        if self.mock_maps:

            route = MOCK_DESTINATIONS.get(

                destination,

                {
                    "distance_km": 5.0,
                    "duration_min": 15,
                    "route_points": None
                }
            )

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

            route = maps_api.get_route(

                # Current/start location
                MOCK_CURRENT_LOCATION["lat"],
                MOCK_CURRENT_LOCATION["lon"],

                # Destination location
                geo["lat"],
                geo["lon"]
            )


            if not route:

                return {
                    "response": generate_response(
                        "no_result"
                    ),
                    "route": None
                }

        response = generate_response(

            "navigate",

            {
                "destination": destination.title(),

                "distance_km": route[
                    "distance_km"
                ],

                "duration_min": route[
                    "duration_min"
                ]
            }
        )

        route_data = {

            # Destination name
            "destination":
                destination.title(),

            "start_lat":
                MOCK_CURRENT_LOCATION["lat"],

            "start_lon":
                MOCK_CURRENT_LOCATION["lon"],

            "end_lat":
                geo["lat"] if geo else None,

            "end_lon":
                geo["lon"] if geo else None,

            "route_points":
                route.get("route_points"),

            "distance_km":
                route["distance_km"],

            "duration_min":
                route["duration_min"]
        }

        return {

            "response": response,

            "route": route_data
        }

    def handle_search_nearby(
        self,
        entities
    ):

        place_type = entities.get(
            "place_type"
        )

        if not place_type:

            return generate_response(
                "no_result"
            )

        if self.mock_maps:

            place = MOCK_NEARBY.get(
                place_type
            )


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

                    # Your current nearby implementation
                    # doesn't calculate actual route distance.
                    "distance_km": 1.0
                }

            else:

                place = None


        if not place:

            return generate_response(
                "no_result"
            )


        return generate_response(

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


    def handle_traffic_info(
        self,
        entities
    ):

        # Currently mocked.
        # A real traffic API can be integrated later.

        import random

        status = random.choice(
            [
                "light",
                "moderate",
                "heavy"
            ]
        )


        return generate_response(

            "traffic_info",

            {
                "traffic_status":
                    status
            }
        )

    def handle_route_preference(
        self,
        entities
    ):

        pref = entities.get(
            "route_preference",
            "your preferred route"
        )


        return generate_response(

            "route_preference",

            {
                "preference":
                    pref.replace(
                        "_",
                        " "
                    )
            }
        )


    def handle_cancel(
        self,
        entities
    ):

        return generate_response(
            "cancel"
        )


    def handle_current_location(
        self,
        entities
    ):

        return generate_response(

            "current_location",

            {
                "place_name":
                    MOCK_CURRENT_LOCATION[
                        "display_name"
                    ]
            }
        )


    def handle_unknown(
        self,
        entities
    ):

        return generate_response(
            "unknown"
        )


    def process(
        self,
        user_text: str
    ) -> dict:

        """
        Run the complete NLP pipeline.

        Returns:

        {
            "input_text": ...,
            "intent": ...,
            "confidence": ...,
            "entities": ...,
            "response": ...,
            "route": ...
        }
        """

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


        entities = extract_entities(
            user_text,
            intent
        )


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


        handler_result = handler(
            entities
        )

        if isinstance(
            handler_result,
            dict
        ):

            response_text = (
                handler_result[
                    "response"
                ]
            )

            route_data = (
                handler_result.get(
                    "route"
                )
            )

        else:

            response_text = (
                handler_result
            )

            route_data = None


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
                response_text,

            "route":
                route_data
        }


def run_cli(
    use_microphone: bool = False
):

    # Use real maps for CLI testing
    pipeline = VoiceAssistantPipeline(
        mock_maps=False
    )


    print("=" * 60)

    print(
        "NLP Voice Assistant"
    )

    print(
        "Google Maps-style Voice Navigation"
    )

    print(
        "Type 'quit' to exit."
    )

    print("=" * 60)


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

            f"Response: "
            f"{result['response']}"
        )

        if result.get("route"):

            route = result["route"]


            print(
                f"Distance: "
                f"{route['distance_km']} km"
            )


            print(
                f"Duration: "
                f"{route['duration_min']} minutes"
            )


            # Number of road coordinates
            if route.get(
                "route_points"
            ):

                print(
                    f"Route points: "
                    f"{len(route['route_points'])}"
                )


        speak(
            result["response"],
            use_audio=False
        )


        print(
            "-" * 60
        )


if __name__ == "__main__":

    run_cli(
        use_microphone=False
    )

