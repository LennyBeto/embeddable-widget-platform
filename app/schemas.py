from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models import WidgetType

MAX_FIELDS = 20
MAX_FIELD_NAME_LEN = 64
MAX_SUBMISSION_VALUE_LEN = 2000


# ---------- Auth ----------

class SignupRequest(BaseModel):
    tenant_name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Widget fields ----------

class WidgetField(BaseModel):
    name: str = Field(..., min_length=1, max_length=MAX_FIELD_NAME_LEN)
    label: str = Field(..., min_length=1, max_length=200)
    field_type: str = Field(default="text")  # text | email | textarea
    required: bool = True


class WidgetCreate(BaseModel):
    type: WidgetType = WidgetType.signup_form
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default="", max_length=1000)
    fields: list[WidgetField] = Field(..., min_length=1, max_length=MAX_FIELDS)
    button_text: str = Field(default="Submit", max_length=50)
    display_options: dict[str, Any] = Field(default_factory=dict)


class WidgetUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    fields: Optional[list[WidgetField]] = Field(default=None, max_length=MAX_FIELDS)
    button_text: Optional[str] = Field(default=None, max_length=50)
    display_options: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None


class WidgetOut(BaseModel):
    id: str
    type: WidgetType
    title: str
    description: Optional[str]
    fields: list[dict]
    button_text: str
    display_options: dict
    is_active: bool
    embed_snippet: str
    created_at: datetime

    class Config:
        from_attributes = True


class WidgetConfigOut(BaseModel):
    """Public, cacheable config served to the browser widget loader."""
    id: str
    type: WidgetType
    title: str
    description: Optional[str]
    fields: list[dict]
    button_text: str
    display_options: dict


# ---------- Public submission ----------

class SubmissionCreate(BaseModel):
    """
    Generic payload: `data` holds the visitor's form fields.
    `hp_field` is the honeypot — real visitors never fill it.
    """
    data: dict[str, str]
    hp_field: Optional[str] = Field(default="", max_length=500)

    @field_validator("data")
    @classmethod
    def bounded_payload(cls, v: dict[str, str]) -> dict[str, str]:
        if not v:
            raise ValueError("data must not be empty")
        if len(v) > MAX_FIELDS:
            raise ValueError(f"too many fields (max {MAX_FIELDS})")
        for key, val in v.items():
            if len(key) > MAX_FIELD_NAME_LEN:
                raise ValueError(f"field name too long: {key[:20]}...")
            if not isinstance(val, str):
                raise ValueError(f"field '{key}' must be a string")
            if len(val) > MAX_SUBMISSION_VALUE_LEN:
                raise ValueError(f"field '{key}' exceeds max length ({MAX_SUBMISSION_VALUE_LEN})")
        return v


class SubmissionOut(BaseModel):
    id: str
    widget_id: str
    data: dict
    country: Optional[str]
    city: Optional[str]
    geo_provider: Optional[str]
    email_side_effect_status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Dashboard ----------

class DashboardStats(BaseModel):
    total_submissions: int
    submissions_by_widget: dict[str, int]
    submissions_by_country: dict[str, int]
    submissions_last_7_days: dict[str, int]
