from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Submission, User, Widget
from app.schemas import DashboardStats, SubmissionOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/submissions", response_model=list[SubmissionOut])
def list_submissions(widget_id: str | None = None, user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    query = db.query(Submission).filter(Submission.tenant_id == user.tenant_id)
    if widget_id:
        query = query.filter(Submission.widget_id == widget_id)
    return query.order_by(Submission.created_at.desc()).all()


@router.get("/stats", response_model=DashboardStats)
def get_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    submissions = db.query(Submission).filter(Submission.tenant_id == user.tenant_id).all()
    widgets = {w.id: w.title for w in db.query(Widget).filter(Widget.tenant_id == user.tenant_id).all()}

    by_widget = Counter(widgets.get(s.widget_id, s.widget_id) for s in submissions)
    by_country = Counter(s.country or "unknown" for s in submissions)

    cutoff = datetime.utcnow() - timedelta(days=7)
    by_day: Counter = Counter()
    for s in submissions:
        if s.created_at >= cutoff:
            by_day[s.created_at.strftime("%Y-%m-%d")] += 1

    return DashboardStats(
        total_submissions=len(submissions),
        submissions_by_widget=dict(by_widget),
        submissions_by_country=dict(by_country),
        submissions_last_7_days=dict(sorted(by_day.items())),
    )
