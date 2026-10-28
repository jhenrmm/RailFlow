from datetime import datetime, timezone

from config import OPEN_METEO_URL, WEATHER_TIMEOUT
from services.http import request_with_retries

_WEATHER_PARAMS: dict[str, str | int] = {
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

    def hourly_value(key: str):
        if key == "time":
            return times[index]
        values = hourly.get(key, [])
        return values[index] if index < len(values) else None

    return {key: hourly_value(key) for key in keys}


def fetch_weather(latitude: float, longitude: float, target_time: datetime | None = None) -> dict:
    params = {"latitude": latitude, "longitude": longitude, **_WEATHER_PARAMS}
    response = request_with_retries("GET", OPEN_METEO_URL, params=params, timeout=WEATHER_TIMEOUT)
    return _context(response.json(), target_time)
