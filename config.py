import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)

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