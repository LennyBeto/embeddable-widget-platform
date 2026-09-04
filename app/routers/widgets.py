from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.cache import set_bundle_cache_headers, set_config_cache_headers
from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import User, Widget
from app.schemas import WidgetCreate, WidgetOut, WidgetUpdate, WidgetConfigOut

router = APIRouter(tags=["widgets"])


def _embed_snippet(widget_id: str, request_host: str) -> str:
    return f'<script src="{request_host}/widget/{settings.widget_bundle_version}/widget.js?id={widget_id}"></script>'


def _to_out(widget: Widget, request_host: str) -> WidgetOut:
    return WidgetOut(
        id=widget.id,
        type=widget.type,
        title=widget.title,
        description=widget.description,
        fields=widget.fields,
        button_text=widget.button_text,
        display_options=widget.display_options,
        is_active=widget.is_active,
        embed_snippet=_embed_snippet(widget.id, request_host),
        created_at=widget.created_at,
    )


def _get_owned_widget_or_404(db: Session, widget_id: str, user: User) -> Widget:
    """The single choke point for tenant isolation on widget routes:
    a widget from another tenant is treated as if it doesn't exist at all."""
    widget = (
        db.query(Widget)
        .filter(Widget.id == widget_id, Widget.tenant_id == user.tenant_id)
        .first()
    )
    if widget is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found")
    return widget


@router.post("/widgets", response_model=WidgetOut, status_code=status.HTTP_201_CREATED)
def create_widget(payload: WidgetCreate, request_host: str = "https://your-domain.com",
                   user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    widget = Widget(
        tenant_id=user.tenant_id,
        type=payload.type,
        title=payload.title,
        description=payload.description or "",
        fields=[f.model_dump() for f in payload.fields],
        button_text=payload.button_text,
        display_options=payload.display_options,
    )
    db.add(widget)
    db.commit()
    db.refresh(widget)
    return _to_out(widget, request_host)


@router.get("/widgets", response_model=list[WidgetOut])
def list_widgets(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    widgets = db.query(Widget).filter(Widget.tenant_id == user.tenant_id).all()
    return [_to_out(w, "https://your-domain.com") for w in widgets]


@router.get("/widgets/{widget_id}", response_model=WidgetOut)
def get_widget(widget_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    widget = _get_owned_widget_or_404(db, widget_id, user)
    return _to_out(widget, "https://your-domain.com")


@router.patch("/widgets/{widget_id}", response_model=WidgetOut)
def update_widget(widget_id: str, payload: WidgetUpdate,
                   user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    widget = _get_owned_widget_or_404(db, widget_id, user)
    updates = payload.model_dump(exclude_unset=True)
    if "fields" in updates and updates["fields"] is not None:
        updates["fields"] = [f if isinstance(f, dict) else f.model_dump() for f in updates["fields"]]
    for key, value in updates.items():
        setattr(widget, key, value)
    db.commit()
    db.refresh(widget)
    return _to_out(widget, "https://your-domain.com")


@router.delete("/widgets/{widget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_widget(widget_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    widget = _get_owned_widget_or_404(db, widget_id, user)
    db.delete(widget)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- Public, cached delivery (no auth — this is what the customer's site calls) ----------

@router.get("/widgets/{widget_id}/config", response_model=WidgetConfigOut)
def get_widget_config(widget_id: str, response: Response, db: Session = Depends(get_db)):
    """Short-lived cache: the owner can edit a widget and see it reflected within ~1 minute."""
    widget = db.query(Widget).filter(Widget.id == widget_id, Widget.is_active.is_(True)).first()
    if widget is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found")
    set_config_cache_headers(response)
    return WidgetConfigOut(
        id=widget.id, type=widget.type, title=widget.title, description=widget.description,
        fields=widget.fields, button_text=widget.button_text, display_options=widget.display_options,
    )
