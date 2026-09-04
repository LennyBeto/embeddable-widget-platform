import os

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session
from slowapi.errors import RateLimitExceeded

from app.cache import set_bundle_cache_headers
from app.config import settings
from app.database import get_db
from app.email_service import send_confirmation
from app.geo import enrich_ip
from app.models import Submission, Widget
from app.rate_limit import limiter, widget_limiter
from app.schemas import SubmissionCreate, SubmissionOut
from app.spam import SpamDetected, check_honeypot

router = APIRouter(tags=["public"])

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")


@router.get("/widget/{version}/widget.js")
def get_widget_bundle(version: str):
    """
    Versioned, long-lived-cache bundle. Bump WIDGET_BUNDLE_VERSION and ship a new
    /widget/v2/widget.js path to cache-bust — v1 keeps serving old embeds untouched.
    """
    path = os.path.join(STATIC_DIR, "widget.v1.js")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Bundle not found")
    # FileResponse builds its own headers, so the cache header must be set on
    # *this* response object, not on an injected Response (which would be replaced).
    file_response = FileResponse(path, media_type="application/javascript")
    set_bundle_cache_headers(file_response)
    return file_response


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post(
    "/widgets/{widget_id}/submissions",
    response_model=SubmissionOut,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(lambda: settings.rate_limit_per_ip)
@widget_limiter.limit(lambda: settings.rate_limit_per_widget)
def submit_widget_form(
    widget_id: str,
    payload: SubmissionCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    The one endpoint the entire public internet can reach. Order of operations
    matters and mirrors the architecture diagram in the README:

      1. widget must exist and be active           -> 404 otherwise
      2. payload shape                              -> 422 (handled by Pydantic before we get here)
      3. spam check (honeypot)                      -> reject silently as 400
      4. geo enrichment (best-effort, never fails)
      5. store
      6. safe side effect (best-effort, never fails the response)
    """
    widget = db.query(Widget).filter(Widget.id == widget_id, Widget.is_active.is_(True)).first()
    if widget is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found")

    try:
        check_honeypot(payload.hp_field)
    except SpamDetected:
        # Deliberately generic + same status family as a normal validation error,
        # so a bot can't distinguish "spam rejected" from "bad payload".
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Submission rejected")

    # Validate submitted field names against the widget's own schema so extra/garbage
    # keys can't be smuggled through, while still accepting any subset of required fields.
    allowed_names = {f["name"] for f in widget.fields}
    unknown = set(payload.data.keys()) - allowed_names
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown field(s): {sorted(unknown)}")
    required = {f["name"] for f in widget.fields if f.get("required", True)}
    missing = required - set(payload.data.keys())
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing required field(s): {sorted(missing)}")

    client_ip = _get_client_ip(request)
    geo = enrich_ip(client_ip)  # never raises — always returns a GeoResult

    submission = Submission(
        widget_id=widget.id,
        tenant_id=widget.tenant_id,
        data=payload.data,
        ip_address=client_ip,
        country=geo.country,
        city=geo.city,
        geo_provider=geo.provider,
        email_side_effect_status="pending",
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    # Safe side effect: wrapped again here even though email_service already
    # catches internally — belt and suspenders around the "never break the main path" rule.
    try:
        status_result = send_confirmation(submission.id, widget.title, payload.data)
    except Exception:  # noqa: BLE001
        status_result = "failed"
    submission.email_side_effect_status = status_result
    db.commit()
    db.refresh(submission)

    return submission
