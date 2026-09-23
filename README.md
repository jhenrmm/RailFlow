# Transito AI

Intelligent trip analysis API built with **FastAPI**. Given an origin and a destination, it computes the best route, fetches live weather along the corridor, and uses a local LLM (via Ollama) to produce a human-readable travel assessment with weather impact and delay risk.

## Features

- **Authentication** — JWT-based register/login/logout with PBKDF2 password hashing and server-side token revocation.
- **Trip analysis** — computes distance, duration and corridor midpoint via the OpenRoute API (supports several travel profiles).
- **Weather context** — fetches current conditions (temperature, humidity, precipitation, wind, etc.) at the origin, destination and midpoint using Open-Meteo (no API key required).
- **AI assessment** — a local Ollama model analyzes the route + weather and returns a JSON assessment with a summary, weather impact, delay risk and recommendation.
- **History** — every analysis is stored per user; a history endpoint lists past analyses.
- **Interactive docs** — automatic OpenAPI docs served at `/docs`.

## Tech stack

| Component | Technology |
| --- | --- |
| API framework | [FastAPI](https://fastapi.tiangolo.com) + Uvicorn |
| Database | PostgreSQL (SQLAlchemy 2.0 + psycopg) |
| Authentication | PyJWT (HS256) + PBKDF2 |
| Routing | [OpenRoute Service](https://openrouteservice.org) |
| Weather | [Open-Meteo](https://open-meteo.com) |
| Local LLM | [Ollama](https://ollama.com) `/api/chat` |

## Project structure

```
.
├── main.py                 # FastAPI app entry point
├── config.py               # Environment configuration
├── database.py             # SQLAlchemy engine/session setup
├── models.py               # ORM models (User, RouteAnalysisHistory, RevokedToken)
├── schemas.py              # Pydantic request/response models
├── routers/
│   ├── auth.py             # /auth endpoints
│   ├── analysis.py         # /analyze/route endpoint
│   └── history.py          # /history endpoint
├── services/
│   ├── security.py         # password hashing, JWTs, token revocation
│   ├── routing.py          # OpenRoute integration
│   ├── weather.py          # Open-Meteo integration
│   └── ai.py               # Ollama integration
└── test/
    └── integration_test.py # End-to-end API test
```

## Requirements

- Python 3.11+
- PostgreSQL (running locally)
- [Ollama](https://ollama.com) with a model pulled (e.g. `ollama pull qwen3:4b`)
- An [OpenRoute API key](https://openrouteservice.org) (free tier available)

## Getting started

### 1. Clone and set up the environment

```bash
git clone <your-repo-url>
cd transito
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env        # Windows
# cp .env.example .env      # macOS/Linux
```

Edit `.env` at minimum:

```ini
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/railflow
OPENROUTE_API_KEY=your-openroute-key-here
```

### 3. Run the API

```bash
uvicorn main:app --reload
```

Open http://localhost:8000/docs for the interactive Swagger UI.

> Tables are created automatically on startup (`Base.metadata.create_all`).

### 4. Run the integration test

```bash
python test/integration_test.py
```

Requires Ollama running and `OPENROUTE_API_KEY` configured. It registers a user, performs a real trip analysis and validates the stored history.

## API endpoints

### Auth

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/auth/register` | Register a new user, returns a JWT (`201`) |
| `POST` | `/auth/login` | Login, returns a JWT |
| `POST` | `/auth/logout` | Revoke the current token |

### Analysis

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/analyze/route` | Analyze a trip. Body: `origin`, `destination` (`lat`/`lon`) and optional `profile`. Requires `Authorization: Bearer <token>` |

Supported `profile` values: `driving-car`, `driving-hgv`, `foot-walking`, `cycling-regular`, `wheelchair`.

Example request:

```bash
curl -X POST http://localhost:8000/analyze/route \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "origin":       {"lat": -23.5213, "lon": -46.1967},
    "destination":  {"lat": -23.5213, "lon": -46.2254},
    "profile": "driving-car"
  }'
```

The response contains the route summary, weather snapshots for the origin/destination/midpoint, and the AI-generated analysis.

### History

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/history` | List the current user's past analyses, newest first |

## Environment variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `DATABASE_URL` | yes | — | SQLAlchemy connection string |
| `OPENROUTE_API_KEY` | yes | — | OpenRoute API key |
| `OPENROUTE_ROUTING_URL` | no | OpenRoute directions v2 | Routing base URL |
| `OPENROUTE_TIMEOUT` | no | `10` | Routing request timeout (s) |
| `OPEN_METEO_URL` | no | Open-Meteo forecast | Weather API URL |
| `WEATHER_TIMEOUT` | no | `10` | Weather request timeout (s) |
| `OLLAMA_URL` | no | `http://localhost:11434` | Ollama base URL |
| `OLLAMA_MODEL` | no | `qwen3:4b` | Ollama model name |
| `OLLAMA_TIMEOUT` | no | `1000` | Ollama request timeout (s) |
| `JWT_SECRET_KEY` | no | dev default | JWT signing secret (set a strong one in production) |
| `JWT_ALGORITHM` | no | `HS256` | JWT signing algorithm |
| `JWT_EXPIRE_MINUTES` | no | `60` | Access token lifetime |

## License

[MIT](LICENSE)