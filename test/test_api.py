from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import main
from database import Base, get_db
from services import ai, rate_limit, routing, weather

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def override_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


def client(monkeypatch):
    rate_limit._attempts.clear()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    main.app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(main, "validate_settings", lambda: None)
    return TestClient(main.app)


def test_route_analysis_and_paginated_history(monkeypatch):
    monkeypatch.setattr(
        routing,
        "fetch_route",
        lambda *_: {
            "distance_m": 10_000,
            "duration_s": 900,
            "coordinates": [
                {"lat": -23.5, "lon": -46.2},
                {"lat": -23.51, "lon": -46.21},
                {"lat": -23.52, "lon": -46.22},
            ],
        },
    )
    monkeypatch.setattr(
        weather,
        "fetch_weather",
        lambda lat, lon, target: {
            "temperature_2m": 22,
            "weather_code": 0,
            "time": target.isoformat(),
        },
    )
    monkeypatch.setattr(
        ai,
        "analyze_trip",
        lambda *_: ai.TripAssessment(
            summary="Clear journey",
            weather_impact="No material impact",
            delay_risk="low",
            recommendation="Travel normally",
        ),
    )
    with client(monkeypatch) as api:
        register = api.post(
            "/auth/register", json={"email": "user@example.com", "password": "safe-password-123"}
        )
        assert register.status_code == 201
        auth = {"Authorization": f"Bearer {register.json()['access_token']}"}
        result = api.post(
            "/analyze/route",
            json={
                "origin": {"lat": -23.5, "lon": -46.2},
                "destination": {"lat": -23.52, "lon": -46.22},
            },
            headers=auth,
        )
        assert result.status_code == 200
        assert result.json()["analysis"]["delay_risk"] == "low"
        assert len(result.json()["weather"]) == 5
        history = api.get("/history?offset=0&limit=1", headers=auth)
        assert history.status_code == 200
        assert history.json()[0]["weather"][0]["location"] == "origin"


def test_rejects_same_origin_and_destination(monkeypatch):
    with client(monkeypatch) as api:
        register = api.post(
            "/auth/register", json={"email": "another@example.com", "password": "safe-password-123"}
        )
        auth = {"Authorization": f"Bearer {register.json()['access_token']}"}
        response = api.post(
            "/analyze/route",
            json={"origin": {"lat": 1, "lon": 1}, "destination": {"lat": 1, "lon": 1}},
            headers=auth,
        )
        assert response.status_code == 422


def test_ai_output_must_match_schema(monkeypatch):
    class Response:
        def json(self):
            return {"message": {"content": "not json"}}

    monkeypatch.setattr(ai, "request_with_retries", lambda *args, **kwargs: Response())
    try:
        ai.analyze_trip({}, [])
    except ai.InvalidAiResponseError as exc:
        assert "valid assessment" in str(exc)
    else:
        raise AssertionError("invalid model output must be rejected")


def test_returns_bad_gateway_for_invalid_route_geometry(monkeypatch):
    monkeypatch.setattr(
        routing,
        "fetch_route",
        lambda *_: {"distance_m": 1, "duration_s": 1, "coordinates": [{"lat": 1, "lon": 1}]},
    )
    with client(monkeypatch) as api:
        register = api.post(
            "/auth/register",
            json={"email": "geometry@example.com", "password": "safe-password-123"},
        )
        auth = {"Authorization": f"Bearer {register.json()['access_token']}"}
        response = api.post(
            "/analyze/route",
            json={"origin": {"lat": 1, "lon": 1}, "destination": {"lat": 2, "lon": 2}},
            headers=auth,
        )

    assert response.status_code == 502
    assert response.json()["detail"] == "Routing service returned unusable route geometry"


def test_ready_returns_service_unavailable_when_database_is_down(monkeypatch):
    monkeypatch.setattr(main, "is_database_ready", lambda: False)
    with client(monkeypatch) as api:
        response = api.get("/ready")

    assert response.status_code == 503


def test_returns_bad_gateway_when_routing_service_fails(monkeypatch):
    monkeypatch.setattr(
        routing, "fetch_route", lambda *_: (_ for _ in ()).throw(RuntimeError("down"))
    )
    with client(monkeypatch) as api:
        register = api.post(
            "/auth/register",
            json={"email": "routing@example.com", "password": "safe-password-123"},
        )
        auth = {"Authorization": f"Bearer {register.json()['access_token']}"}
        response = api.post(
            "/analyze/route",
            json={"origin": {"lat": 1, "lon": 1}, "destination": {"lat": 2, "lon": 2}},
            headers=auth,
        )

    assert response.status_code == 502
    assert response.json()["detail"] == "Routing service unavailable"


def test_returns_bad_gateway_when_weather_service_fails(monkeypatch):
    monkeypatch.setattr(
        routing,
        "fetch_route",
        lambda *_: {
            "distance_m": 1_000,
            "duration_s": 60,
            "coordinates": [{"lat": 1, "lon": 1}, {"lat": 2, "lon": 2}],
        },
    )
    monkeypatch.setattr(
        weather, "fetch_weather", lambda *_: (_ for _ in ()).throw(RuntimeError("down"))
    )
    with client(monkeypatch) as api:
        register = api.post(
            "/auth/register",
            json={"email": "weather@example.com", "password": "safe-password-123"},
        )
        auth = {"Authorization": f"Bearer {register.json()['access_token']}"}
        response = api.post(
            "/analyze/route",
            json={"origin": {"lat": 1, "lon": 1}, "destination": {"lat": 2, "lon": 2}},
            headers=auth,
        )

    assert response.status_code == 502
    assert response.json()["detail"] == "Weather service unavailable"


def test_rejects_invalid_token(monkeypatch):
    with client(monkeypatch) as api:
        response = api.get("/history", headers={"Authorization": "Bearer invalid"})

    assert response.status_code == 401


def test_limits_authentication_attempts(monkeypatch):
    rate_limit._attempts.clear()
    with client(monkeypatch) as api:
        for number in range(5):
            response = api.post(
                "/auth/register",
                json={
                    "email": f"limit-{number}@example.com",
                    "password": "safe-password-123",
                },
            )
            assert response.status_code == 201
        response = api.post(
            "/auth/register",
            json={"email": "limit-six@example.com", "password": "safe-password-123"},
        )

    assert response.status_code == 429
