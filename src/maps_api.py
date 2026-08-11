"""
Maps API integration.

Uses:
- Nominatim (OpenStreetMap) -> place name to coordinates
- OSRM -> actual driving route
"""

import time
import requests


# ============================================================
# API URLs
# ============================================================

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

OSRM_URL = "https://router.project-osrm.org/route/v1/driving"


# ============================================================
# REQUEST HEADERS
# ============================================================

HEADERS = {
    "User-Agent": "NLP-Voice-Navigation-Assistant/1.0"
}


# ============================================================
# Nominatim rate limiter
# ============================================================

_last_request_time = 0


def _rate_limit():

    global _last_request_time

    elapsed = time.time() - _last_request_time

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
    Convert place name into latitude and longitude.
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


        result = results[0]

        return {

            "lat":
                float(result["lat"]),

            "lon":
                float(result["lon"]),

            "display_name":
                result["display_name"]
        }


    except requests.RequestException as e:

        print(
            f"[Geocoding error] {e}"
        )

        return None


# ============================================================
# GET ACTUAL DRIVING ROUTE
# ============================================================

def get_route(
    origin_lat,
    origin_lon,
    dest_lat,
    dest_lon
):

    """
    Get actual driving route from OSRM.

    Returns:
        distance
        duration
        route coordinates
    """


    # --------------------------------------------------------
    # OSRM URL
    # --------------------------------------------------------

    url = (
        f"{OSRM_URL}/"
        f"{origin_lon},{origin_lat};"
        f"{dest_lon},{dest_lat}"
    )


    # --------------------------------------------------------
    # IMPORTANT
    # overview = full
    # geometries = geojson
    #
    # This gives us the complete road route.
    # --------------------------------------------------------

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


        # ----------------------------------------------------
        # Check OSRM response
        # ----------------------------------------------------

        if data.get("code") != "Ok":

            print(
                "[OSRM] Route not found"
            )

            return None


        if not data.get("routes"):

            return None


        route = data["routes"][0]


        # ----------------------------------------------------
        # Distance
        # ----------------------------------------------------

        distance_km = round(
            route["distance"] / 1000,
            2
        )


        # ----------------------------------------------------
        # Duration
        # ----------------------------------------------------

        duration_min = round(
            route["duration"] / 60,
            1
        )


        # ----------------------------------------------------
        # ROUTE GEOMETRY
        # ----------------------------------------------------

        geometry = route.get(
            "geometry"
        )


        if not geometry:

            return None


        coordinates = geometry.get(
            "coordinates",
            []
        )


        # ----------------------------------------------------
        # OSRM gives:
        #
        # [longitude, latitude]
        #
        # Folium needs:
        #
        # [latitude, longitude]
        # ----------------------------------------------------

        route_points = [

            [
                point[1],
                point[0]
            ]

            for point in coordinates

            if len(point) >= 2
        ]


        # ----------------------------------------------------
        # TURN-BY-TURN STEPS
        # ----------------------------------------------------

        steps = []


        for leg in route.get(
            "legs",
            []
        ):

            for step in leg.get(
                "steps",
                []
            ):

                maneuver = step.get(
                    "maneuver",
                    {}
                )

                instruction_type = maneuver.get(
                    "type",
                    ""
                )

                modifier = maneuver.get(
                    "modifier",
                    ""
                )

                name = step.get(
                    "name",
                    ""
                )

                distance = round(
                    step.get(
                        "distance",
                        0
                    ) / 1000,
                    2
                )


                instruction = (
                    f"{instruction_type}"
                )


                if modifier:

                    instruction += (
                        f" {modifier}"
                    )


                if name:

                    instruction += (
                        f" onto {name}"
                    )


                steps.append({

                    "instruction":
                        instruction,

                    "road":
                        name,

                    "distance_km":
                        distance
                })


        # ----------------------------------------------------
        # RETURN COMPLETE ROUTE
        # ----------------------------------------------------

        return {

            "distance_km":
                distance_km,

            "duration_min":
                duration_min,

            "route_points":
                route_points,

            "steps":
                steps
        }


    except requests.RequestException as e:

        print(
            f"[OSRM routing error] {e}"
        )

        return None


# ============================================================
# FIND NEARBY PLACE
# ============================================================

def find_nearby_place(
    place_type: str,
    lat: float,
    lon: float
):

    """
    Find a nearby place using Nominatim.
    """

    _rate_limit()


    query_map = {

        "hospital":
            "hospital",

        "atm":
            "atm",

        "fuel_station":
            "petrol pump",

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
            "EV charging station"
    }


    query = query_map.get(
        place_type,
        place_type
    )


    params = {

        "q":
            query,

        "format":
            "json",

        "limit":
            5,

        "viewbox":
            (
                f"{lon - 0.05},"
                f"{lat + 0.05},"
                f"{lon + 0.05},"
                f"{lat - 0.05}"
            ),

        "bounded":
            1
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


        result = results[0]


        return {

            "lat":
                float(result["lat"]),

            "lon":
                float(result["lon"]),

            "display_name":
                result["display_name"]
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
        "\nTesting geocoding..."
    )

    start = geocode(
        "Vijayawada, India"
    )

    destination = geocode(
        "Guntur, India"
    )


    print(
        "\nSTART:"
    )

    print(
        start
    )


    print(
        "\nDESTINATION:"
    )

    print(
        destination
    )


    if start and destination:

        print(
            "\nGetting driving route..."
        )

        route = get_route(

            start["lat"],
            start["lon"],

            destination["lat"],
            destination["lon"]
        )


        print(
            "\nROUTE:"
        )

        print(
            route
        )
