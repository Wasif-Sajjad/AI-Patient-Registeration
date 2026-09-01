import re
import uuid
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL",
    "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT",
    "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI",
    "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
}

NAME_RE = re.compile(r"^[A-Za-z\-']+$")
ZIP_RE = re.compile(r"^\d{5}(-\d{4})?$")


class Sex(str, Enum):
    male = "Male"
    female = "Female"
    other = "Other"
    decline = "Decline to Answer"


def _validate_name(v: str) -> str:
    if not (1 <= len(v) <= 50) or not NAME_RE.match(v):
        raise ValueError("must be 1-50 alphabetic characters (hyphens/apostrophes allowed)")
    return v


def _validate_phone(v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    digits = re.sub(r"\D", "", v)
    if len(digits) != 10:
        raise ValueError("must be a valid US 10-digit phone number")
    return digits


class PatientBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    sex: Sex
    phone_number: str
    email: Optional[EmailStr] = None
    address_line_1: str = Field(min_length=1, max_length=255)
    address_line_2: Optional[str] = Field(default=None, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    state: str
    zip_code: str
    insurance_provider: Optional[str] = Field(default=None, max_length=255)
    insurance_member_id: Optional[str] = Field(default=None, max_length=100)
    preferred_language: str = Field(default="English", max_length=50)
    emergency_contact_name: Optional[str] = Field(default=None, max_length=255)
    emergency_contact_phone: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, v: str) -> str:
        return _validate_name(v)

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone_required(cls, v: str) -> str:
        result = _validate_phone(v)
        assert result is not None
        return result

    @field_validator("emergency_contact_phone")
    @classmethod
    def validate_phone_optional(cls, v: Optional[str]) -> Optional[str]:
        return _validate_phone(v)

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str) -> str:
        v = v.strip().upper()
        if v not in US_STATES:
            raise ValueError("must be a valid 2-letter US state abbreviation")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v: str) -> str:
        if not ZIP_RE.match(v.strip()):
            raise ValueError("must be a 5-digit or ZIP+4 US zip code")
        return v.strip()


class PatientCreate(PatientBase):
    """Payload for POST /patients."""


class PatientUpdate(BaseModel):
    """Payload for PUT /patients/:id — every field optional (partial update)."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    sex: Optional[Sex] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, v: Optional[str]) -> Optional[str]:
        return _validate_name(v) if v is not None else v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        return v

    @field_validator("phone_number", "emergency_contact_phone")
    @classmethod
    def validate_phones(cls, v: Optional[str]) -> Optional[str]:
        return _validate_phone(v)

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().upper()
        if v not in US_STATES:
            raise ValueError("must be a valid 2-letter US state abbreviation")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not ZIP_RE.match(v.strip()):
            raise ValueError("must be a 5-digit or ZIP+4 US zip code")
        return v.strip()


class PatientOut(PatientBase):
    model_config = ConfigDict(from_attributes=True)

    patient_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class Envelope(BaseModel):
    """Every API response uses this shape: { "data": ..., "error": null }."""

    data: Optional[Any] = None
    error: Optional[str] = None
