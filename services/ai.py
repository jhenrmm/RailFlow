import json

import httpx

from config import OLLAMA_MODEL, OLLAMA_TIMEOUT, OLLAMA_URL

SYSTEM_PROMPT = (
    "You are an expert in transportation and meteorology. Given a trip's route "
    "summary and the current weather along the corridor, analyze the expected "
    "travel conditions. Respond ONLY with JSON using these keys: "
    "\"summary\" (overall assessment), \"weather_impact\" (how the weather may "
    "affect the trip), \"delay_risk\" (one of: low, moderate, high), and "
    "\"recommendation\" (practical advice for the traveler)."
)


def build_prompt(route: dict, weather: list[dict]) -> str:
    return (
        "Analyze the following trip based on its route summary and current "
        "weather along the corridor (origin, destination and midpoint).\n\n"
        f"ROUTE:\n{json.dumps(route, ensure_ascii=False, indent=2)}\n\n"
        f"WEATHER:\n{json.dumps(weather, ensure_ascii=False, indent=2)}"
    )


def analyze_trip(route: dict, weather: list[dict]) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(route, weather)},
        ],
        "options": {"temperature": 0.3},
    }
    resp = httpx.post(
        f"{OLLAMA_URL.rstrip('/')}/api/chat",
        json=payload,
        timeout=OLLAMA_TIMEOUT,
    )
    resp.raise_for_status()

    body = resp.json()
    if "error" in body:
        raise ValueError(f"Ollama error: {body['error']}")
    content = body.get("message", {}).get("content")
    if not content:
        raise ValueError(
            f"Unexpected Ollama response keys: {sorted(body.keys())}"
        )
    return content