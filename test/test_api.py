from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import main
from database import Base, get_db
from services import ai, routing, weather

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def override_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


def client(monkeypatch):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    main.app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(main, "validate_settings", lambda: None)
    return TestClient(main.app)


def test_route_analysis_and_paginated_history(monkeypatch):
    monkeypatch.setattr(routing, "fetch_route", lambda *_: {
        "distance_m": 10_000, "duration_s": 900,
        "coordinates": [
            {"lat": -23.5, "lon": -46.2}, {"lat": -23.51, "lon": -46.21}, {"lat": -23.52, "lon": -46.22},
        ],
    })
    monkeypatch.setattr(weather, "fetch_weather", lambda lat, lon, target: {
        "temperature_2m": 22, "weather_code": 0, "time": target.isoformat(),
    })
    monkeypatch.setattr(ai, "analyze_trip", lambda *_: ai.TripAssessment(
        summary="Clear journey", weather_impact="No material impact", delay_risk="low", recommendation="Travel normally"
    ))
    with client(monkeypatch) as api:
        register = api.post("/auth/register", json={"email": "user@example.com", "password": "safe-password-123"})
        assert register.status_code == 201
        auth = {"Authorization": f"Bearer {register.json()['access_token']}"}
        result = api.post("/analyze/route", json={"origin": {"lat": -23.5, "lon": -46.2}, "destination": {"lat": -23.52, "lon": -46.22}}, headers=auth)
        assert result.status_code == 200
        assert result.json()["analysis"]["delay_risk"] == "low"
        assert len(result.json()["weather"]) == 5
        history = api.get("/history?offset=0&limit=1", headers=auth)
        assert history.status_code == 200
        assert history.json()[0]["weather"][0]["location"] == "origin"


def test_rejects_same_origin_and_destination(monkeypatch):
    with client(monkeypatch) as api:
        register = api.post("/auth/register", json={"email": "another@example.com", "password": "safe-password-123"})
        auth = {"Authorization": f"Bearer {register.json()['access_token']}"}
        response = api.post("/analyze/route", json={"origin": {"lat": 1, "lon": 1}, "destination": {"lat": 1, "lon": 1}}, headers=auth)
        assert response.status_code == 422


def test_ai_output_must_match_schema(monkeypatch):
    class Response:
        def raise_for_status(self): pass
        def json(self): return {"message": {"content": "not json"}}
    monkeypatch.setattr(ai.httpx, "post", lambda *args, **kwargs: Response())
    try:
        ai.analyze_trip({}, [])
    except ValueError as exc:
        assert "invalid assessment" in str(exc)
    else:
        raise AssertionError("invalid model output must be rejected")
