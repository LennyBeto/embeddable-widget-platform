import uuid
import enum
from datetime import datetime

from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Enum, Boolean, JSON, Integer, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Tenant(Base):
    """A customer account. Every widget and submission is scoped to exactly one tenant."""
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    widgets = relationship("Widget", back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    """A widget owner who logs in and manages their tenant's widgets."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    tenant_id = Column(UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="users")


class WidgetType(str, enum.Enum):
    signup_form = "signup_form"
    cta_popover = "cta_popover"


class Widget(Base):
    """A customer-configured embeddable widget. Tenant-isolated."""
    __tablename__ = "widgets"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    tenant_id = Column(UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False, index=True)
    type = Column(Enum(WidgetType), nullable=False, default=WidgetType.signup_form)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True, default="")
    fields = Column(JSON, nullable=False, default=list)  # e.g. [{"name": "email", "label": "Email", "required": true}]
    button_text = Column(String, nullable=False, default="Submit")
    display_options = Column(JSON, nullable=False, default=dict)  # e.g. {"theme": "light", "position": "bottom-right"}
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="widgets")
    submissions = relationship("Submission", back_populates="widget", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_widgets_tenant_active", "tenant_id", "is_active"),
    )


class Submission(Base):
    """A single visitor submission captured from a public, cross-origin form."""
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    widget_id = Column(UUID(as_uuid=False), ForeignKey("widgets.id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False, index=True)
    data = Column(JSON, nullable=False)  # validated form fields
    ip_address = Column(String, nullable=True)
    country = Column(String, nullable=True)
    city = Column(String, nullable=True)
    geo_provider = Column(String, nullable=True)  # which provider answered, or null
    email_side_effect_status = Column(String, nullable=False, default="pending")  # sent | failed | skipped
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    widget = relationship("Widget", back_populates="submissions")

    __table_args__ = (
        Index("ix_submissions_tenant_created", "tenant_id", "created_at"),
    )
