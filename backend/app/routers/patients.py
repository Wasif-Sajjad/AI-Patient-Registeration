import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.patient import Envelope, PatientCreate, PatientOut, PatientUpdate
from app.services import patient_service
from app.services.patient_service import NotFoundError

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("", response_model=Envelope)
async def list_patients(
    last_name: Optional[str] = Query(default=None),
    date_of_birth: Optional[str] = Query(default=None),
    phone_number: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    patients = await patient_service.list_patients(
        db, last_name=last_name, date_of_birth=date_of_birth, phone_number=phone_number
    )
    data = [PatientOut.model_validate(p).model_dump(mode="json") for p in patients]
    return Envelope(data=data, error=None)


@router.get("/{patient_id}", response_model=Envelope)
async def get_patient(patient_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        patient = await patient_service.get_patient(db, patient_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return Envelope(data=PatientOut.model_validate(patient).model_dump(mode="json"), error=None)


@router.post("", response_model=Envelope, status_code=status.HTTP_201_CREATED)
async def create_patient(payload: PatientCreate, db: AsyncSession = Depends(get_db)):
    patient = await patient_service.create_patient(db, payload)
    return Envelope(data=PatientOut.model_validate(patient).model_dump(mode="json"), error=None)


@router.put("/{patient_id}", response_model=Envelope)
async def update_patient(
    patient_id: uuid.UUID, payload: PatientUpdate, db: AsyncSession = Depends(get_db)
):
    try:
        patient = await patient_service.update_patient(db, patient_id, payload)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return Envelope(data=PatientOut.model_validate(patient).model_dump(mode="json"), error=None)


@router.delete("/{patient_id}", response_model=Envelope)
async def delete_patient(patient_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        patient = await patient_service.soft_delete_patient(db, patient_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return Envelope(
        data={"patient_id": str(patient.patient_id), "deleted_at": patient.deleted_at.isoformat()},
        error=None,
    )
