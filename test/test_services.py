from datetime import datetime, timezone

import pytest

from services import ai, routing, weather
from services.http import UpstreamServiceError


def test_extracts_geojson_route():
    extracted = routing._extract(
        {
            "features": [
                {
                    "properties": {"summary": {"distance": 1234, "duration": 321}},
                    "geometry": {"coordinates": [[-46.2, -23.5], [-46.3, -23.6]]},
                }
            ]
        }
    )

    assert extracted == {
        "distance_m": 1234,
        "duration_s": 321,
        "coordinates": [{"lat": -23.5, "lon": -46.2}, {"lat": -23.6, "lon": -46.3}],
    }


def test_weather_uses_closest_hourly_forecast():
    data = {
        "current": {"temperature_2m": 10},
        "hourly": {
            "time": ["2026-01-01T10:00", "2026-01-01T11:00"],
            "temperature_2m": [20, 21],
            "weather_code": [1, 2],
        },
    }

    result = weather._context(data, datetime(2026, 1, 1, 10, 40, tzinfo=timezone.utc))

    assert result["time"] == "2026-01-01T11:00"
    assert result["temperature_2m"] == 21
    assert result["weather_code"] == 2


def test_retries_invalid_ai_output_until_valid(monkeypatch):
    responses = iter(
        [
            {"message": {"content": "not json"}},
            {
                "message": {
                    "content": (
                        '{"summary":"Clear","weather_impact":"None",'
                        '"delay_risk":"low","recommendation":"Travel normally"}'
                    )
                }
            },
        ]
    )

    class Response:
        def __init__(self, body):
            self._body = body

        def json(self):
            return self._body

    monkeypatch.setattr(
        ai,
        "request_with_retries",
        lambda *args, **kwargs: Response(next(responses)),
    )

    result = ai.analyze_trip({}, [])

    assert result.delay_risk == "low"


def test_reports_invalid_ai_output_after_bounded_retries(monkeypatch):
    class Response:
        def json(self):
            return {"message": {"content": "not json"}}

    monkeypatch.setattr(ai, "request_with_retries", lambda *args, **kwargs: Response())

    with pytest.raises(ai.InvalidAiResponseError):
        ai.analyze_trip({}, [])


def test_upstream_errors_are_exposed_as_service_error(monkeypatch):
    monkeypatch.setattr(
        routing,
        "request_with_retries",
        lambda *args, **kwargs: (_ for _ in ()).throw(UpstreamServiceError("down")),
    )

    with pytest.raises(UpstreamServiceError):
        routing.fetch_route(
            type("Coordinates", (), {"lat": 1, "lon": 2})(),
            type("Coordinates", (), {"lat": 3, "lon": 4})(),
            "driving-car",
        )
