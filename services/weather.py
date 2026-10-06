from datetime import datetime, timezone

import httpx

from config import OPEN_METEO_URL, WEATHER_TIMEOUT

_WEATHER_PARAMS = {
    "current": (
        "temperature_2m,relative_humidity_2m,apparent_temperature,"
        "weather_code,precipitation,wind_speed_10m,wind_direction_10m"
    ),
    # UTC makes forecast-time matching deterministic across the corridor.
    "timezone": "UTC",
    "hourly": (
        "temperature_2m,apparent_temperature,relative_humidity_2m,"
        "precipitation,weather_code,wind_speed_10m,wind_direction_10m"
    ),
    "forecast_days": 2,
}


def _context(data: dict, target_time: datetime | None = None) -> dict:
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
    if target_time is None:
        return {key: current.get(key) for key in keys}
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    if not times:
        return {key: current.get(key) for key in keys}
    target = target_time.astimezone(timezone.utc).replace(tzinfo=None)
    index = min(
        range(len(times)),
        key=lambda i: abs(datetime.fromisoformat(times[i]) - target).total_seconds(),
    )
    return {
        key: (times[index] if key == "time" else hourly.get(key, [None])[index]) for key in keys
    }


def fetch_weather(latitude: float, longitude: float, target_time: datetime | None = None) -> dict:
    params = {"latitude": latitude, "longitude": longitude, **_WEATHER_PARAMS}
    last_error = None
    for _ in range(3):
        try:
            resp = httpx.get(OPEN_METEO_URL, params=params, timeout=WEATHER_TIMEOUT)
            resp.raise_for_status()
            return _context(resp.json(), target_time)
        except httpx.HTTPError as exc:
            last_error = exc
    raise last_error or RuntimeError("Weather request failed")
