import httpx

from config import OPEN_METEO_URL, WEATHER_TIMEOUT

_WEATHER_PARAMS = {
    "current": (
        "temperature_2m,relative_humidity_2m,apparent_temperature,"
        "weather_code,precipitation,wind_speed_10m,wind_direction_10m"
    ),
    "timezone": "auto",
    "forecast_days": 1,
}


def _context(data: dict) -> dict:
    current = data.get("current", {})
    keys = (
        "temperature_2m",
        "apparent_temperature",
        "relative_humidity_2m",
        "precipitation",
        "weather_code",
        "wind_speed_10m",
        "wind_direction_10m",
        "time",
    )
    return {key: current.get(key) for key in keys}


def fetch_weather(latitude: float, longitude: float) -> dict:
    params = {"latitude": latitude, "longitude": longitude, **_WEATHER_PARAMS}
    resp = httpx.get(OPEN_METEO_URL, params=params, timeout=WEATHER_TIMEOUT)
    resp.raise_for_status()
    return _context(resp.json())