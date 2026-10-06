import httpx

from config import OPENROUTE_API_KEY, OPENROUTE_ROUTING_URL, OPENROUTE_TIMEOUT

PROFILES = (
    "driving-car",
    "driving-hgv",
    "cycling-regular",
    "cycling-road",
    "cycling-mountain",
    "cycling-electric",
    "foot-walking",
    "foot-hiking",
    "wheelchair",
)


def _extract(data: dict) -> dict:
    if "features" in data:
        feature = data["features"][0]
        summary = feature["properties"]["summary"]
        coords = feature["geometry"]["coordinates"]
        mid_lon, mid_lat = coords[len(coords) // 2]
    else:
        route = data["routes"][0]
        summary = route["summary"]
        geometry = route.get("geometry")
        if isinstance(geometry, dict) and geometry.get("coordinates"):
            coords = geometry["coordinates"]
            mid_lon, mid_lat = coords[len(coords) // 2]
        else:
            raise ValueError("OpenRoute returned an unknown geometry format")

    return {
        "distance_m": summary["distance"],
        "duration_s": summary["duration"],
        "coordinates": [{"lat": lat, "lon": lon} for lon, lat in coords],
    }


def fetch_route(origin, destination, profile: str) -> dict:
    if not OPENROUTE_API_KEY:
        raise ValueError("OPENROUTE_API_KEY is not configured in .env")
    if profile not in PROFILES:
        raise ValueError(f"Unsupported profile '{profile}'")
    start = f"{origin.lon},{origin.lat}"
    end = f"{destination.lon},{destination.lat}"
    url = f"{OPENROUTE_ROUTING_URL}/{profile}?api_key={OPENROUTE_API_KEY}&start={start}&end={end}&format=geojson"
    last_error = None
    for _ in range(3):
        try:
            resp = httpx.get(url, timeout=OPENROUTE_TIMEOUT)
            resp.raise_for_status()
            return _extract(resp.json())
        except httpx.HTTPError as exc:
            last_error = exc
    raise last_error or RuntimeError("Routing request failed")
