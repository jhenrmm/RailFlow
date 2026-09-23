import sys

sys.path.insert(0, r"C:\Users\hohot\OneDrive\Desktop\transito")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import main

from database import Base, get_db

eng = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(eng)
S = sessionmaker(bind=eng, autocommit=False, autoflush=False)


def override_db():
    db = S()
    try:
        yield db
    finally:
        db.close()


main.app.dependency_overrides[get_db] = override_db
client = TestClient(main.app)

r = client.post(
    "/auth/register",
    json={"email": "user@example.com", "password": "senha-longa-123"},
)
assert r.status_code == 201, r.text
tok = r.json()["access_token"]
print("register OK")

r = client.post(
    "/analyze/route",
    json={
        "origin": {"lat": -23.52134475519342, "lon": -46.1967707873158},
        "destination": {"lat": -23.52134475519342, "lon": -46.225499157170866},
    },
    headers={"Authorization": f"Bearer {tok}"},
)
print("analyze ->", r.status_code)
assert r.status_code == 200, r.text
body = r.json()
print("distance_km:", body["route"]["distance_km"])
print("analysis head:", body["analysis"][:140].replace(chr(10), " "))
assert body["analysis"].strip(), "empty analysis"
assert '"delay_risk"' in body["analysis"] or "delay_risk" in body["analysis"]

r = client.get("/history", headers={"Authorization": f"Bearer {tok}"})
assert r.status_code == 200, r.text
entries = r.json()
assert len(entries) == 1 and entries[0]["user_id"] == 1
print("history OK, rows:", len(entries))

print("FULL REAL INTEGRATION PASSED")