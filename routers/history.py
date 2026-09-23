from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import RouteAnalysisHistory, User
from schemas import HistoryEntry
from services import security

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=list[HistoryEntry])
def list_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user),
):
    return (
        db.query(RouteAnalysisHistory)
        .filter(RouteAnalysisHistory.user_id == current_user.id)
        .order_by(RouteAnalysisHistory.created_at.desc())
        .all()
    )