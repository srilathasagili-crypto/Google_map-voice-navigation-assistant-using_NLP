"""
Maps integration using:

- Nominatim → finds coordinates
- OSRM → calculates driving route
- OSRM steps → turn-by-turn directions

No API key required.
"""

import time
import requests


# ============================================================
# API URLs
# ============================================================

NOMINATIM_URL = (
    "https://nominatim.openstreetmap.org/search"
)

OSRM_URL = (
    "https://router.project-osrm.org/route/v1/driving"
)


HEADERS = {
    "User-Agent": "NLP-Voice-Navigation-Assistant/1.0"
}


# ============================================================
# Nominatim rate limiting
# ============================================================

_last_request_time = 0


def _rate_limit():

    global _last_request_time

    elapsed = (
        time.time() - _last_request_time
    )

    if elapsed < 1.1:

        time.sleep(
            1.1 - elapsed
        )

    _last_request_time = time.time()


# ============================================================
# GEOCODING
# ============================================================

def geocode(place_name: str):

    """
    Convert a place name into latitude/longitude.
    """

    _rate_limit()

    params = {

        "q": place_name,

        "format": "json",

        "limit": 1
    }


    try:

        response = requests.get(

            NOMINATIM_URL,

            params=params,

            headers=HEADERS,

            timeout=15
        )


        response.raise_for_status()

        results = response.json()


        if not results:

            return None


        return {

            "lat":
                float(results[0]["lat"]),

            "lon":
                float(results[0]["lon"]),

            "display_name":
                results[0]["display_name"]
        }


    except requests.RequestException as e:

        print(
            f"[Geocoding error] {e}"
        )

        return None


# ============================================================
# ROUTING
# ============================================================

def get_route(
    origin_lat,
    origin_lon,
    dest_lat,
    dest_lon
):

    """
    Get driving route from origin
    to destination.

    Returns:

    - distance
    - duration
    - route geometry
    - turn-by-turn steps
    """


    url = (

        f"{OSRM_URL}/"

        f"{origin_lon},{origin_lat};"

        f"{dest_lon},{dest_lat}"
    )


    params = {

        "overview": "full",

        "geometries": "geojson",

        "steps": "true"
    }


    try:

        response = requests.get(

            url,

            params=params,

            timeout=20
        )


        response.raise_for_status()

        data = response.json()


        if data.get("code") != "Ok":

            return None


        route = data["routes"][0]


        # ====================================================
        # DISTANCE
        # ====================================================

        distance_km = round(

            route["distance"] / 1000,

            2
        )


        # ====================================================
        # DURATION
        # ====================================================

        duration_min = round(

            route["duration"] / 60,

            1
        )


        # ====================================================
        # ROUTE GEOMETRY
        # ====================================================

        coordinates = (

            route
            .get("geometry", {})
            .get("coordinates", [])
        )


        route_points = [

            [lat, lon]

            for lon, lat
            in coordinates
        ]


        # ====================================================
        # TURN-BY-TURN DIRECTIONS
        # ====================================================

        directions = []


        legs = route.get(
            "legs",
            []
        )


        for leg in legs:

            steps = leg.get(
                "steps",
                []
            )


            for step in steps:

                maneuver = step.get(
                    "maneuver",
                    {}
                )


                instruction = (
                    maneuver.get(
                        "type",
                        ""
                    )
                )


                modifier = (
                    maneuver.get(
                        "modifier",
                        ""
                    )
                )


                road_name = (
                    step.get(
                        "name",
                        ""
                    )
                )


                # --------------------------------------------
                # Create readable instruction
                # --------------------------------------------

                if instruction == "depart":

                    text = (
                        "Start your journey"
                    )


                elif instruction == "arrive":

                    text = (
                        "Arrive at your destination"
                    )


                elif instruction == "turn":

                    if modifier:

                        text = (
                            f"Turn "
                            f"{modifier}"
                        )

                    else:

                        text = (
                            "Turn"
                        )


                elif instruction == "continue":

                    text = (
                        "Continue straight"
                    )


                elif instruction == "roundabout":

                    text = (
                        "Enter the roundabout"
                    )


                elif instruction == "new name":

                    text = (
                        "Continue"
                    )


                else:

                    text = (
                        instruction
                        .replace(
                            "_",
                            " "
                        )
                        .capitalize()
                    )


                # --------------------------------------------
                # Add road name
                # --------------------------------------------

                if road_name:

                    text += (
                        f" on {road_name}"
                    )


                directions.append({

                    "instruction":
                        text,

                    "distance_m":
                        round(
                            step.get(
                                "distance",
                                0
                            )
                        ),

                    "duration_sec":
                        round(
                            step.get(
                                "duration",
                                0
                            )
                        )
                })


        # ====================================================
        # FINAL RESULT
        # ====================================================

        return {

            "distance_km":
                distance_km,

            "duration_min":
                duration_min,

            "route_points":
                route_points,

            "directions":
                directions
        }


    except requests.RequestException as e:

        print(
            f"[Routing error] {e}"
        )

        return None


# ============================================================
# NEARBY SEARCH
# ============================================================

def find_nearby_place(
    place_type: str,
    lat: float,
    lon: float
):

    """
    Search for a nearby place using Nominatim.
    """

    _rate_limit()


    query_map = {

        "hospital":
            "hospital",

        "atm":
            "atm",

        "fuel_station":
            "fuel station",

        "pharmacy":
            "pharmacy",

        "restaurant":
            "restaurant",

        "cafe":
            "cafe",

        "bank":
            "bank",

        "parking":
            "parking",

        "grocery":
            "supermarket",

        "charging_station":
            "ev charging station"
    }


    query = query_map.get(

        place_type,

        place_type
    )


    params = {

        "q": query,

        "format": "json",

        "limit": 1,

        "viewbox": (
            f"{lon - 0.05},"
            f"{lat + 0.05},"
            f"{lon + 0.05},"
            f"{lat - 0.05}"
        ),

        "bounded": 1
    }


    try:

        response = requests.get(

            NOMINATIM_URL,

            params=params,

            headers=HEADERS,

            timeout=15
        )


        response.raise_for_status()

        results = response.json()


        if not results:

            return None


        return {

            "lat":
                float(
                    results[0]["lat"]
                ),

            "lon":
                float(
                    results[0]["lon"]
                ),

            "display_name":
                results[0][
                    "display_name"
                ]
        }


    except requests.RequestException as e:

        print(
            f"[Nearby search error] {e}"
        )

        return None


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "Testing Vijayawada..."
    )


    vijayawada = geocode(
        "Vijayawada, India"
    )


    print(
        "Vijayawada:",
        vijayawada
    )


    print(
        "Testing Guntur..."
    )


    guntur = geocode(
        "Guntur, India"
    )


    print(
        "Guntur:",
        guntur
    )


    if vijayawada and guntur:

        route = get_route(

            vijayawada["lat"],

            vijayawada["lon"],

            guntur["lat"],

            guntur["lon"]
        )


        print(
            "\nRoute:"
        )

        print(
            route
        )
