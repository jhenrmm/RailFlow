import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Open-Meteo (clima, sem chave)
OPEN_METEO_URL = os.getenv(
    "OPEN_METEO_URL", "https://api.open-meteo.com/v1/forecast"
)
WEATHER_TIMEOUT = float(os.getenv("WEATHER_TIMEOUT", "10"))

# OpenRoute (rotas)
OPENROUTE_API_KEY = os.getenv("OPENROUTE_API_KEY")
OPENROUTE_ROUTING_URL = os.getenv(
    "OPENROUTE_ROUTING_URL",
    "https://api.heigit.org/openrouteservice/v2/directions",
)
OPENROUTE_TIMEOUT = float(os.getenv("OPENROUTE_TIMEOUT", "10"))

# Ollama local
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "1000"))

# JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

# HTTP/API behaviour
ALLOWED_ORIGINS = [
    origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "").split(",") if origin.strip()
]
RATE_LIMIT_ATTEMPTS = int(os.getenv("RATE_LIMIT_ATTEMPTS", "5"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))


@lru_cache
def validate_settings() -> None:
    """Fail early with actionable messages rather than during a request."""
    missing = [
        name
        for name, value in {
            "DATABASE_URL": DATABASE_URL,
            "OPENROUTE_API_KEY": OPENROUTE_API_KEY,
            "JWT_SECRET_KEY": JWT_SECRET_KEY,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError("Missing required environment variables: " + ", ".join(missing))
