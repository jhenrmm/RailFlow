import json
import logging
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import RouteAnalysisHistory, User
from schemas import (
    RouteAnalysisRequest,
    RouteAnalysisResponse,
    RouteSummary,
    WeatherSnapshot,
)
from services import ai, geo, routing, security, weather

logger = logging.getLogger("transito")

router = APIRouter(prefix="/analyze", tags=["analysis"])


@router.post("/route", response_model=RouteAnalysisResponse)
def analyze_route(
    req: RouteAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user),
):
    try:
        route = routing.fetch_route(req.origin, req.destination, req.profile)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("Routing service failed")
        raise HTTPException(status_code=502, detail="Routing service unavailable")

    try:
        points = geo.sample_corridor_points(route)
    except geo.InvalidRouteGeometryError as exc:
        logger.warning("Routing service returned unusable geometry: %s", exc)
        raise HTTPException(
            status_code=502, detail="Routing service returned unusable route geometry"
        )

    snapshots: list[WeatherSnapshot] = []
    try:
        departure = datetime.now(timezone.utc)

        def fetch(point):
            label, lat, lon, progress = point
            arrival = departure + timedelta(seconds=route["duration_s"] * progress)
            data = weather.fetch_weather(lat, lon, arrival)
            return WeatherSnapshot(location=label, latitude=lat, longitude=lon, **data)

        with ThreadPoolExecutor(max_workers=len(points)) as executor:
            snapshots = list(executor.map(fetch, points))
    except Exception:
        logger.exception("Weather service failed")
        raise HTTPException(status_code=502, detail="Weather service unavailable")

    route_context = {
        "profile": req.profile,
        "distance_m": int(route["distance_m"]),
        "duration_s": int(route["duration_s"]),
    }
    weather_context = [
        {
            "location": snap.location,
            "latitude": snap.latitude,
            "longitude": snap.longitude,
            **snap.model_dump(exclude={"location", "latitude", "longitude"}),
        }
        for snap in snapshots
    ]

    try:
        analysis = ai.analyze_trip(route_context, weather_context)
    except Exception as exc:
        logger.error(
            "Ollama chat failed (model=%s): %s\n%s",
            ai.OLLAMA_MODEL,
            exc,
            traceback.format_exc(),
        )
        raise HTTPException(status_code=502, detail="AI service unavailable")

    history = RouteAnalysisHistory(
        user_id=current_user.id,
        origin_lat=req.origin.lat,
        origin_lon=req.origin.lon,
        destination_lat=req.destination.lat,
        destination_lon=req.destination.lon,
        profile=req.profile,
        distance_m=route["distance_m"],
        duration_s=route["duration_s"],
        weather_json=json.dumps(weather_context, ensure_ascii=False),
        analysis=analysis.model_dump_json(),
        model=ai.OLLAMA_MODEL,
    )
    db.add(history)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Could not save route analysis")
        raise HTTPException(status_code=500, detail="Could not save route analysis")

    return RouteAnalysisResponse(
        route=RouteSummary(
            profile=req.profile,
            distance_km=round(route["distance_m"] / 1000, 2),
            duration_min=round(route["duration_s"] / 60, 1),
        ),
        weather=snapshots,
        analysis=analysis,
        model=ai.OLLAMA_MODEL,
    )
