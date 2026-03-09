"""Pydantic schemas for Deal (commercial contract) endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# Valid incoterm values matching the SQL enum
IncotermType = Literal[
    "FOB", "CIF", "CFR", "EXW", "FCA", "CPT", "CIP", "DAP", "DPU", "DDP"
]

# Valid deal status values matching the SQL enum
DealStatusType = Literal[
    "draft", "confirmed", "loading", "in_transit", "arrived", "completed", "cancelled"
]


class DealCreate(BaseModel):
    """Request body for creating a new deal."""

    contract_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unique contract identifier, e.g. CHR-2026-0042",
        examples=["CHR-2026-0042"],
    )
    commodity: str = Field(default="charcoal", max_length=100)
    buyer: str = Field(..., min_length=1, max_length=200)
    seller: str = Field(..., min_length=1, max_length=200)
    quantity_tons: float = Field(..., gt=0, description="Cargo quantity in metric tons")
    price_per_ton: float = Field(..., gt=0, description="Price per metric ton in USD")
    incoterms: IncotermType = "FOB"
    load_port_id: UUID
    discharge_port_id: UUID
    status: DealStatusType = "draft"
    notes: str | None = None


class DealUpdate(BaseModel):
    """Request body for updating an existing deal. All fields optional."""

    commodity: str | None = Field(default=None, max_length=100)
    buyer: str | None = Field(default=None, max_length=200)
    seller: str | None = Field(default=None, max_length=200)
    quantity_tons: float | None = Field(default=None, gt=0)
    price_per_ton: float | None = Field(default=None, gt=0)
    incoterms: IncotermType | None = None
    load_port_id: UUID | None = None
    discharge_port_id: UUID | None = None
    status: DealStatusType | None = None
    notes: str | None = None


class PortSummary(BaseModel):
    """Embedded port summary within a deal response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    country: str
    unlocode: str


class DealResponse(BaseModel):
    """Full deal response including computed contract value."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    contract_id: str
    commodity: str
    buyer: str
    seller: str
    quantity_tons: float
    price_per_ton: float
    contract_value: float | None = None
    incoterms: IncotermType
    load_port_id: UUID
    discharge_port_id: UUID
    load_port: PortSummary | None = None
    discharge_port: PortSummary | None = None
    status: DealStatusType
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class DealListResponse(BaseModel):
    """Paginated list of deals."""

    items: list[DealResponse]
    total: int
    page: int
    page_size: int
