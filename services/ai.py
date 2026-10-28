import json

from config import OLLAMA_MODEL, OLLAMA_TIMEOUT, OLLAMA_URL
from schemas import TripAssessment
from services.http import UpstreamServiceError, request_with_retries

SYSTEM_PROMPT = (
    "You are an expert in transportation and meteorology. Given a trip's route "
    "summary and the current weather along the corridor, analyze the expected "
    "travel conditions. Respond ONLY with JSON using these keys: "
    '"summary" (overall assessment), "weather_impact" (how the weather may '
    'affect the trip), "delay_risk" (one of: low, moderate, high), and '
    '"recommendation" (practical advice for the traveler).'
)


def build_prompt(route: dict, weather: list[dict]) -> str:
    return (
        "Analyze the following trip based on its route summary and current "
        "weather along the corridor (origin, destination and midpoint).\n\n"
        f"ROUTE:\n{json.dumps(route, ensure_ascii=False, indent=2)}\n\n"
        f"WEATHER:\n{json.dumps(weather, ensure_ascii=False, indent=2)}"
    )


def _parse_assessment(content: str) -> TripAssessment:
    """Reject hallucinated prose or malformed model output at the boundary."""
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        return TripAssessment.model_validate_json(cleaned)
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError("Ollama returned an invalid assessment") from exc


class InvalidAiResponseError(ValueError):
    """Ollama responded, but did not produce a valid trip assessment."""


def analyze_trip(route: dict, weather: list[dict]) -> TripAssessment:
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(route, weather)},
        ],
        "options": {"temperature": 0.3},
    }
    last_error: Exception | None = None
    for _ in range(3):
        try:
            response = request_with_retries(
                "POST",
                f"{OLLAMA_URL.rstrip('/')}/api/chat",
                json=payload,
                timeout=OLLAMA_TIMEOUT,
                attempts=1,
            )
            body = response.json()
            if "error" in body:
                raise InvalidAiResponseError(f"Ollama error: {body['error']}")
            content = body.get("message", {}).get("content")
            if not content:
                raise InvalidAiResponseError(
                    f"Unexpected Ollama response keys: {sorted(body.keys())}"
                )
            return _parse_assessment(content)
        except (UpstreamServiceError, ValueError, json.JSONDecodeError) as exc:
            last_error = exc
    raise InvalidAiResponseError("Ollama did not return a valid assessment") from last_error
