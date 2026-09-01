import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate


class NotFoundError(Exception):
    pass


async def create_patient(db: AsyncSession, payload: PatientCreate) -> Patient:
    patient = Patient(**payload.model_dump())
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient


async def get_patient(db: AsyncSession, patient_id: uuid.UUID) -> Patient:
    stmt = select(Patient).where(
        Patient.patient_id == patient_id, Patient.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()
    if patient is None:
        raise NotFoundError(f"patient {patient_id} not found")
    return patient


async def list_patients(
    db: AsyncSession,
    last_name: Optional[str] = None,
    date_of_birth: Optional[str] = None,
    phone_number: Optional[str] = None,
) -> Sequence[Patient]:
    stmt = select(Patient).where(Patient.deleted_at.is_(None))
    if last_name:
        stmt = stmt.where(Patient.last_name.ilike(last_name))
    if date_of_birth:
        stmt = stmt.where(Patient.date_of_birth == date_of_birth)
    if phone_number:
        digits = "".join(ch for ch in phone_number if ch.isdigit())
        stmt = stmt.where(Patient.phone_number == digits)
    stmt = stmt.order_by(Patient.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


async def find_by_phone(db: AsyncSession, phone_number: str) -> Optional[Patient]:
    digits = "".join(ch for ch in phone_number if ch.isdigit())
    stmt = select(Patient).where(
        Patient.phone_number == digits, Patient.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_patient(
    db: AsyncSession, patient_id: uuid.UUID, payload: PatientUpdate
) -> Patient:
    patient = await get_patient(db, patient_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(patient, field, value)
    await db.commit()
    await db.refresh(patient)
    return patient


async def soft_delete_patient(db: AsyncSession, patient_id: uuid.UUID) -> Patient:
    patient = await get_patient(db, patient_id)
    patient.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(patient)
    return patient
