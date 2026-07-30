"""
Maps API integration: geocoding via Nominatim (OpenStreetMap) and
routing via OSRM (Open Source Routing Machine) — both free, public APIs.

Note: Nominatim's public endpoint has a strict usage policy (max 1 request/
second, requires a descriptive User-Agent). For a resume project this is
fine; for real production use you'd self-host Nominatim/OSRM or use a
paid provider with higher rate limits.
"""

import time
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"

HEADERS = {"User-Agent": "NLP-Voice-Assistant-Project/1.0"}

_last_request_time = 0


def _rate_limit():
    """Nominatim requires max 1 req/sec — enforce a small delay."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < 1.1:
        time.sleep(1.1 - elapsed)
    _last_request_time = time.time()


def geocode(place_name: str):
    """Convert a place name/destination string into lat/lon coordinates."""
    _rate_limit()
    params = {"q": place_name, "format": "json", "limit": 1}
    try:
        resp = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        results = resp.json()
        if not results:
            return None
        return {
            "lat": float(results[0]["lat"]),
            "lon": float(results[0]["lon"]),
            "display_name": results[0]["display_name"],
        }
    except requests.RequestException as e:
        print(f"[geocode error] {e}")
        return None


def get_route(origin_lat, origin_lon, dest_lat, dest_lon):
    """Get driving route + duration/distance between two coordinates via OSRM."""
    url = f"{OSRM_URL}/{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
    params = {"overview": "false"}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != "Ok":
            return None
        route = data["routes"][0]
        return {
            "distance_km": round(route["distance"] / 1000, 2),
            "duration_min": round(route["duration"] / 60, 1),
        }
    except requests.RequestException as e:
        print(f"[routing error] {e}")
        return None


def find_nearby_place(place_type: str, lat: float, lon: float):
    """
    Search for a nearby place of a given type using Nominatim's search,
    biased around the user's current location.
    """
    _rate_limit()
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
        "charging_station": "ev charging station",
    }
    query = query_map.get(place_type, place_type)
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "viewbox": f"{lon-0.05},{lat+0.05},{lon+0.05},{lat-0.05}",
        "bounded": 1,
    }
    try:
        resp = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        results = resp.json()
        if not results:
            return None
        return {
            "lat": float(results[0]["lat"]),
            "lon": float(results[0]["lon"]),
            "display_name": results[0]["display_name"],
        }
    except requests.RequestException as e:
        print(f"[nearby search error] {e}")
        return None


if __name__ == "__main__":
    # Quick manual test (requires internet access)
    result = geocode("Charminar, Hyderabad")
    print("Geocode test:", result)
