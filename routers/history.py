import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from models import RouteAnalysisHistory, User
from schemas import HistoryEntry, TripAssessment, WeatherSnapshot
from services import security

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=list[HistoryEntry])
def list_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    rows = (
        db.query(RouteAnalysisHistory)
        .filter(RouteAnalysisHistory.user_id == current_user.id)
        .order_by(RouteAnalysisHistory.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        HistoryEntry(
            id=row.id, user_id=row.user_id, origin_lat=row.origin_lat,
            origin_lon=row.origin_lon, destination_lat=row.destination_lat,
            destination_lon=row.destination_lon, profile=row.profile,
            distance_m=row.distance_m, duration_s=row.duration_s,
            weather=[WeatherSnapshot.model_validate(item) for item in json.loads(row.weather_json)],
            analysis=TripAssessment.model_validate_json(row.analysis),
            model=row.model, created_at=row.created_at,
        )
        for row in rows
    ]
