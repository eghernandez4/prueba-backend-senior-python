"""
Pydantic schemas for data validation and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class ProductType(str, Enum):
    """Supported credit product types."""

    PHONE = "PHONE"
    TWIST = "TWIST"
    CARD = "CARD"


class ApplicationStatus(str, Enum):
    """Credit application evaluation statuses."""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ApplicationBase(BaseModel):
    """Base schema with common application fields and strict validations."""

    amount: int = Field(
        ...,
        gt=0, # greater than
        description="Monto solicitado en COP",
        examples=[1_200_000],
    )
    monthly_income: int = Field(
        ...,
        gt=0,
        description="Ingresos mensuales en COP",
        examples=[4_000_000],
    )
    employment_months: int = Field(
        ...,
        ge=0, # greater than or equal to
        description="Antigüedad laboral en meses",
        examples=[18],
    )
    external_score: int = Field(
        ...,
        ge=0,
        le=1000,
        description="Score externo (0–1000)",
        examples=[750],
    )
    product: ProductType = Field(
        ...,
        description="Tipo de producto: PHONE, TWIST o CARD",
        examples=[ProductType.PHONE],
    )


class ApplicationCreate(ApplicationBase):
    """Schema for incoming application creation payloads."""

    model_config = ConfigDict(extra="forbid")


class EvaluationResult(BaseModel):
    """Evaluation outcome produced by evaluation strategies."""

    status: ApplicationStatus
    rejection_reasons: List[str] = Field(default_factory=list)


class ApplicationResponse(ApplicationBase):
    """Schema for application response representation."""

    id: int
    status: ApplicationStatus
    rejection_reasons: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
