"""
Maps API integration:

- Geocoding via Nominatim (OpenStreetMap)
- Routing via OSRM (Open Source Routing Machine)
- Nearby place search via Nominatim

Both Nominatim and OSRM are free public services.

For the navigation feature, get_route() returns:
    - distance_km
    - duration_min
    - route_points

route_points can be used by Folium to draw the actual
road route on a Streamlit map.
"""

import time
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

OSRM_URL = "https://router.project-osrm.org/route/v1/driving"

# Nominatim requires a descriptive User-Agent.
HEADERS = {
    "User-Agent": "NLP-Voice-Assistant-Project/1.0"
}


_last_request_time = 0


def _rate_limit():
    """
    Nominatim's public service has a strict usage policy.
    Keep at least ~1 second between requests.
    """

    global _last_request_time

    elapsed = time.time() - _last_request_time

    if elapsed < 1.1:
        time.sleep(1.1 - elapsed)

    _last_request_time = time.time()


def geocode(place_name: str):
    """
    Convert a place name into latitude and longitude.

    Example:

        geocode("Charminar, Hyderabad")

    Returns:

        {
            "lat": 17.3616,
            "lon": 78.4747,
            "display_name": "..."
        }

    Returns None if the place cannot be found.
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
            timeout=10
        )

        response.raise_for_status()

        results = response.json()

        if not results:
            return None

        return {
            "lat": float(results[0]["lat"]),
            "lon": float(results[0]["lon"]),
            "display_name": results[0]["display_name"]
        }

    except requests.RequestException as e:

        print(f"[geocode error] {e}")

        return None


def get_route(
    origin_lat,
    origin_lon,
    dest_lat,
    dest_lon
):
    """
    Get driving route between origin and destination
    using OSRM.

    Returns:

        {
            "distance_km": float,
            "duration_min": float,
            "route_points": [(lat, lon), ...]
        }

    route_points contains the actual road geometry and
    can be used by Folium to draw the route.
    """

    # OSRM expects:
    # longitude,latitude

    url = (
        f"{OSRM_URL}/"
        f"{origin_lon},{origin_lat};"
        f"{dest_lon},{dest_lat}"
    )

    params = {
        # Request complete route geometry
        "overview": "full",

        # GeoJSON gives us coordinate points
        "geometries": "geojson"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        # Check whether OSRM successfully calculated route
        if data.get("code") != "Ok":

            print(
                f"[routing error] "
                f"OSRM returned: {data.get('code')}"
            )

            return None

        # Get first route
        route = data["routes"][0]


        coordinates = route["geometry"]["coordinates"]

        # OSRM format:
        #
        # [longitude, latitude]
        #
        # Folium format:
        #
        # [latitude, longitude]
        #
        # Therefore we reverse each coordinate pair.

        route_points = [
            (lat, lon)
            for lon, lat in coordinates
        ]

        return {
            "distance_km": round(
                route["distance"] / 1000,
                2
            ),

            "duration_min": round(
                route["duration"] / 60,
                1
            ),

            "route_points": route_points
        }

    except requests.RequestException as e:

        print(f"[routing error] {e}")

        return None


def find_nearby_place(
    place_type: str,
    lat: float,
    lon: float
):
    """
    Search for a nearby place using Nominatim.

    Example:

        find_nearby_place(
            "hospital",
            17.3850,
            78.4867
        )

    Returns:

        {
            "lat": ...,
            "lon": ...,
            "display_name": "..."
        }

    Returns None if no place is found.
    """

    _rate_limit()

    # Map user-friendly names to search terms
    query_map = {

        "hospital": "hospital",

        "atm": "atm",

        "fuel_station": "fuel station",

        "pharmacy": "pharmacy",

        "restaurant": "restaurant",

        "cafe": "cafe",

        "bank": "bank",

        "parking": "parking",

        "grocery": "supermarket",

        "charging_station": "ev charging station"
    }

    query = query_map.get(
        place_type,
        place_type
    )

    # Search around current location
    params = {

        "q": query,

        "format": "json",

        "limit": 1,

        # Bounding box around current location
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
            timeout=10
        )

        response.raise_for_status()

        results = response.json()

        if not results:
            return None

        return {

            "lat": float(
                results[0]["lat"]
            ),

            "lon": float(
                results[0]["lon"]
            ),

            "display_name": results[0][
                "display_name"
            ]
        }

    except requests.RequestException as e:

        print(
            f"[nearby search error] {e}"
        )

        return None

if __name__ == "__main__":

    print("=" * 60)

    print(
        "Testing Nominatim Geocoding..."
    )

    print("=" * 60)

    result = geocode(
        "Charminar, Hyderabad"
    )

    print(
        "Geocode result:"
    )

    print(result)

    if result:

        print()
        print("=" * 60)

        print(
            "Testing OSRM Routing..."
        )

        print("=" * 60)

        # Your current mock starting location
        start_lat = 17.3850
        start_lon = 78.4867

        route = get_route(
            start_lat,
            start_lon,
            result["lat"],
            result["lon"]
        )

        print(
            "Route result:"
        )

        print(route)

        if route:

            print()
            print(
                f"Distance: "
                f"{route['distance_km']} km"
            )

            print(
                f"Duration: "
                f"{route['duration_min']} minutes"
            )

            print(
                f"Route points: "
                f"{len(route['route_points'])}"
            )

