"""
Main pipeline for the NLP Voice Navigation Assistant.

Flow:

Voice/Text
    ↓
Intent Classification
    ↓
Named Entity Recognition
    ↓
Geocoding using Nominatim
    ↓
Routing using OSRM
    ↓
Route + Turn-by-Turn Directions
    ↓
Response
"""

from intent_classifier import IntentClassifier
from ner_rules import extract_entities
from response_templates import generate_response

import maps_api


# ============================================================
# MOCK SETTINGS
# ============================================================

MOCK_MAPS = False


# ============================================================
# MOCK LOCATION
# ============================================================

MOCK_CURRENT_LOCATION = {

    "lat": 17.3850,

    "lon": 78.4867,

    "display_name":
        "Hyderabad, India"
}


# ============================================================
# MOCK NEARBY PLACES
# ============================================================

MOCK_NEARBY = {

    "hospital": {
        "display_name":
            "City Care Hospital",

        "distance_km":
            1.4
    },

    "atm": {
        "display_name":
            "SBI ATM, Main Road",

        "distance_km":
            0.6
    },

    "fuel_station": {
        "display_name":
            "HP Petrol Pump",

        "distance_km":
            2.1
    },

    "pharmacy": {
        "display_name":
            "Apollo Pharmacy",

        "distance_km":
            0.9
    },

    "restaurant": {
        "display_name":
            "Paradise Restaurant",

        "distance_km":
            1.8
    },

    "cafe": {
        "display_name":
            "Cafe Coffee Day",

        "distance_km":
            0.5
    },

    "bank": {
        "display_name":
            "HDFC Bank Branch",

        "distance_km":
            1.1
    },

    "parking": {
        "display_name":
            "Public Parking Lot",

        "distance_km":
            0.3
    },

    "grocery": {
        "display_name":
            "More Supermarket",

        "distance_km":
            1.0
    },

    "charging_station": {
        "display_name":
            "Tata Power EV Charging Point",

        "distance_km":
            3.0
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

        self.intent_classifier = (
            IntentClassifier(
                confidence_threshold=0.35
            )
        )

        self.mock_maps = mock_maps


    # ========================================================
    # NAVIGATION
    # ========================================================

    def handle_navigate(
        self,
        entities
    ):

        """
        Handles navigation.

        Examples:

        navigate to Charminar

        navigate from Vijayawada to Guntur

        directions from Hyderabad to Warangal
        """


        # ----------------------------------------------------
        # Get origin
        # ----------------------------------------------------

        origin = entities.get(
            "origin"
        )


        # ----------------------------------------------------
        # Get destination
        # ----------------------------------------------------

        destination = entities.get(
            "destination"
        )


        if not destination:

            return (
                generate_response(
                    "no_result"
                ),
                None
            )


        # ====================================================
        # CASE 1
        # Origin + Destination
        # ====================================================

        if origin:

            origin_geo = (
                maps_api.geocode(
                    origin
                )
            )


        # ====================================================
        # CASE 2
        # Only Destination
        #
        # Use Hyderabad as demo
        # starting location.
        # ====================================================

        else:

            origin_geo = {

                "lat":
                    MOCK_CURRENT_LOCATION[
                        "lat"
                    ],

                "lon":
                    MOCK_CURRENT_LOCATION[
                        "lon"
                    ],

                "display_name":
                    MOCK_CURRENT_LOCATION[
                        "display_name"
                    ]
            }

            origin = (
                MOCK_CURRENT_LOCATION[
                    "display_name"
                ]
            )


        # ----------------------------------------------------
        # Check origin
        # ----------------------------------------------------

        if not origin_geo:

            return (
                f"I couldn't find the starting "
                f"location '{origin}'. "
                f"Please try another place.",
                None
            )


        # ----------------------------------------------------
        # Find destination
        # ----------------------------------------------------

        destination_geo = (
            maps_api.geocode(
                destination
            )
        )


        if not destination_geo:

            return (
                f"I couldn't find the destination "
                f"'{destination}'. "
                f"Please try another place.",
                None
            )


        # ====================================================
        # MOCK MODE
        # ====================================================

        if self.mock_maps:

            return (

                (
                    f"Directions from "
                    f"{origin.title()} "
                    f"to "
                    f"{destination.title()}"
                ),

                {

                    "distance_km":
                        5.0,

                    "duration_min":
                        15,

                    "route_points":
                        [],

                    "directions":
                        [],

                    "start_lat":
                        origin_geo["lat"],

                    "start_lon":
                        origin_geo["lon"],

                    "end_lat":
                        destination_geo["lat"],

                    "end_lon":
                        destination_geo["lon"],

                    "destination":
                        destination.title(),

                    "origin":
                        origin.title()
                }
            )


        # ====================================================
        # REAL OSRM ROUTING
        # ====================================================

        route = maps_api.get_route(

            origin_geo["lat"],

            origin_geo["lon"],

            destination_geo["lat"],

            destination_geo["lon"]
        )


        if not route:

            return (

                "I couldn't calculate a route "
                "between those locations. "
                "Please try again.",

                None
            )


        # ----------------------------------------------------
        # Add coordinates
        # ----------------------------------------------------

        route["start_lat"] = (
            origin_geo["lat"]
        )

        route["start_lon"] = (
            origin_geo["lon"]
        )

        route["end_lat"] = (
            destination_geo["lat"]
        )

        route["end_lon"] = (
            destination_geo["lon"]
        )

        route["destination"] = (
            destination.title()
        )

        route["origin"] = (
            origin.title()
        )


        # ====================================================
        # RESPONSE TEXT
        # ====================================================

        response = (

            f"Directions from "
            f"{origin.title()} "
            f"to "
            f"{destination.title()}. "
            f"The distance is "
            f"{route['distance_km']} "
            f"kilometers and the estimated "
            f"travel time is "
            f"{route['duration_min']} minutes."
        )


        return response, route


    # ========================================================
    # NEARBY SEARCH
    # ========================================================

    def handle_search_nearby(
        self,
        entities
    ):

        place_type = entities.get(
            "place_type"
        )


        if not place_type:

            return (
                generate_response(
                    "no_result"
                ),
                None
            )


        # ----------------------------------------------------
        # MOCK
        # ----------------------------------------------------

        if self.mock_maps:

            place = (
                MOCK_NEARBY.get(
                    place_type
                )
            )


        # ----------------------------------------------------
        # REAL
        # ----------------------------------------------------

        else:

            result = (
                maps_api.find_nearby_place(

                    place_type,

                    MOCK_CURRENT_LOCATION[
                        "lat"
                    ],

                    MOCK_CURRENT_LOCATION[
                        "lon"
                    ]
                )
            )


            if result:

                place = {

                    "display_name":
                        result[
                            "display_name"
                        ],

                    "distance_km":
                        1.0
                }

            else:

                place = None


        if not place:

            return (

                generate_response(
                    "no_result"
                ),

                None
            )


        response = generate_response(

            "search_nearby",

            {

                "place_type":
                    place_type.replace(
                        "_",
                        " "
                    ),

                "place_name":
                    place[
                        "display_name"
                    ],

                "distance_km":
                    place[
                        "distance_km"
                    ]
            }
        )


        return response, None


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


        return (

            generate_response(

                "traffic_info",

                {
                    "traffic_status":
                        status
                }
            ),

            None
        )


    # ========================================================
    # ROUTE PREFERENCE
    # ========================================================

    def handle_route_preference(
        self,
        entities
    ):

        pref = entities.get(

            "route_preference",

            "your preferred route"
        )


        return (

            generate_response(

                "route_preference",

                {

                    "preference":
                        pref.replace(
                            "_",
                            " "
                        )
                }
            ),

            None
        )


    # ========================================================
    # CANCEL
    # ========================================================

    def handle_cancel(
        self,
        entities
    ):

        return (

            generate_response(
                "cancel"
            ),

            None
        )


    # ========================================================
    # CURRENT LOCATION
    # ========================================================

    def handle_current_location(
        self,
        entities
    ):

        return (

            generate_response(

                "current_location",

                {

                    "place_name":
                        MOCK_CURRENT_LOCATION[
                            "display_name"
                        ]
                }
            ),

            None
        )


    # ========================================================
    # UNKNOWN
    # ========================================================

    def handle_unknown(
        self,
        entities
    ):

        return (

            generate_response(
                "unknown"
            ),

            None
        )


    # ========================================================
    # MAIN PROCESS
    # ========================================================

    def process(
        self,
        user_text: str
    ) -> dict:

        """
        Runs the complete NLP pipeline.
        """


        # ----------------------------------------------------
        # INTENT CLASSIFICATION
        # ----------------------------------------------------

        intent_result = (
            self.intent_classifier.predict(
                user_text
            )
        )


        intent = (
            intent_result["intent"]
        )


        confidence = (
            intent_result["confidence"]
        )


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
        # RUN HANDLER
        # ----------------------------------------------------

        response_text, route = (
            handler(
                entities
            )
        )


        # ----------------------------------------------------
        # RETURN RESULT
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
                response_text,

            "route":
                route
        }


# ============================================================
# CLI
# ============================================================

def run_cli(
    use_microphone=False
):

    from speech_io import listen, speak


    pipeline = (
        VoiceAssistantPipeline(
            mock_maps=False
        )
    )


    print(
        "=" * 60
    )

    print(
        "NLP Voice Navigation Assistant"
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


        result = (
            pipeline.process(
                user_text
            )
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


        if result["route"]:

            print(
                "\nDistance:",
                result["route"][
                    "distance_km"
                ],
                "km"
            )


            print(
                "Duration:",
                result["route"][
                    "duration_min"
                ],
                "minutes"
            )


            print(
                "\nDirections:"
            )


            for i, step in enumerate(

                result["route"][
                    "directions"
                ],

                1
            ):

                print(

                    f"{i}. "
                    f"{step['instruction']} "
                    f"({step['distance_m']} m)"
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
