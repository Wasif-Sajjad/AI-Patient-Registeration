"""create patients table

Revision ID: 0001
Revises:
Create Date: 2026-09-01

"""
import uuid
from datetime import date, datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "patients",
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("first_name", sa.String(length=50), nullable=False),
        sa.Column("last_name", sa.String(length=50), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("sex", sa.String(length=20), nullable=False),
        sa.Column("phone_number", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("address_line_1", sa.String(length=255), nullable=False),
        sa.Column("address_line_2", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("state", sa.String(length=2), nullable=False),
        sa.Column("zip_code", sa.String(length=10), nullable=False),
        sa.Column("insurance_provider", sa.String(length=255), nullable=True),
        sa.Column("insurance_member_id", sa.String(length=100), nullable=True),
        sa.Column("preferred_language", sa.String(length=50), nullable=False, server_default="English"),
        sa.Column("emergency_contact_name", sa.String(length=255), nullable=True),
        sa.Column("emergency_contact_phone", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_patients_phone_number", "patients", ["phone_number"])

    # --- Optional seed data for demo/review purposes ---
    patients_table = sa.table(
        "patients",
        sa.column("patient_id", postgresql.UUID(as_uuid=True)),
        sa.column("first_name", sa.String),
        sa.column("last_name", sa.String),
        sa.column("date_of_birth", sa.Date),
        sa.column("sex", sa.String),
        sa.column("phone_number", sa.String),
        sa.column("email", sa.String),
        sa.column("address_line_1", sa.String),
        sa.column("city", sa.String),
        sa.column("state", sa.String),
        sa.column("zip_code", sa.String),
        sa.column("preferred_language", sa.String),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    now = datetime.now(timezone.utc)
    op.bulk_insert(
        patients_table,
        [
            {
                "patient_id": uuid.uuid4(),
                "first_name": "Jane",
                "last_name": "Doe",
                "date_of_birth": date(1990, 5, 14),
                "sex": "Female",
                "phone_number": "5551234567",
                "email": "jane.doe@example.com",
                "address_line_1": "123 Main St",
                "city": "Austin",
                "state": "TX",
                "zip_code": "73301",
                "preferred_language": "English",
                "created_at": now,
                "updated_at": now,
            },
            {
                "patient_id": uuid.uuid4(),
                "first_name": "Carlos",
                "last_name": "Alvarez",
                "date_of_birth": date(1985, 11, 2),
                "sex": "Male",
                "phone_number": "5559876543",
                "email": None,
                "address_line_1": "456 Oak Ave",
                "city": "Miami",
                "state": "FL",
                "zip_code": "33101",
                "preferred_language": "Spanish",
                "created_at": now,
                "updated_at": now,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_patients_phone_number", table_name="patients")
    op.drop_table("patients")
