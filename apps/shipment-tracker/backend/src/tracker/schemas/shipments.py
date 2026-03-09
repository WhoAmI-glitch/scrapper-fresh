"""Pydantic schemas for Shipment endpoints."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


ShipmentStatusType = Literal[
    "loading", "departed", "in_transit", "arriving", "arrived", "discharged"
]

RiskLevelType = Literal["low", "medium", "high", "critical"]

IncotermType = Literal[
    "FOB", "CIF", "CFR", "EXW", "FCA", "CPT", "CIP", "DAP", "DPU", "DDP"
]


class ShipmentCreate(BaseModel):
    """Request body for creating a new shipment."""

    deal_id: UUID
    vessel_id: UUID | None = None
    cargo_quantity_tons: float = Field(..., gt=0)
    bill_of_lading: str | None = Field(default=None, max_length=100)
    load_date: date | None = None
    departure_date: datetime | None = None
    eta: datetime | None = None
    status: ShipmentStatusType = "loading"


class ShipmentUpdate(BaseModel):
    """Request body for updating a shipment. All fields optional."""

    vessel_id: UUID | None = None
    cargo_quantity_tons: float | None = Field(default=None, gt=0)
    bill_of_lading: str | None = None
    load_date: date | None = None
    departure_date: datetime | None = None
    eta: datetime | None = None
    actual_arrival: datetime | None = None
    status: ShipmentStatusType | None = None


class ShipmentResponse(BaseModel):
    """Full shipment response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    deal_id: UUID
    vessel_id: UUID | None = None
    cargo_quantity_tons: float
    bill_of_lading: str | None = None
    load_date: date | None = None
    departure_date: datetime | None = None
    eta: datetime | None = None
    actual_arrival: datetime | None = None
    status: ShipmentStatusType
    current_risk_level: RiskLevelType = "low"
    created_at: datetime
    updated_at: datetime


class ActiveShipmentResponse(BaseModel):
    """Denormalised response matching the active_shipments SQL view.

    Includes deal, vessel, and port data in a flat structure
    for efficient dashboard rendering.
    """

    model_config = ConfigDict(from_attributes=True)

    # Shipment fields
    id: UUID
    cargo_quantity_tons: float
    status: ShipmentStatusType
    eta: datetime | None = None
    current_risk_level: RiskLevelType = "low"
    bill_of_lading: str | None = None
    load_date: date | None = None
    departure_date: datetime | None = None

    # Deal fields
    contract_id: str
    buyer: str
    seller: str
    contract_value: float | None = None
    commodity: str
    incoterms: IncotermType

    # Vessel fields
    vessel_name: str | None = None
    imo_number: str | None = None
    mmsi: str | None = None
    vessel_lat: float | None = None
    vessel_lon: float | None = None
    current_speed: float | None = None
    current_heading: float | None = None
    last_ais_update: datetime | None = None

    # Load port
    load_port_name: str
    load_port_code: str
    load_port_lat: float
    load_port_lon: float

    # Discharge port
    discharge_port_name: str
    discharge_port_code: str
    discharge_port_lat: float
    discharge_port_lon: float


class DashboardMetrics(BaseModel):
    """Response for the dashboard metrics view."""

    active_shipments: int = 0
    total_tons_at_sea: float = 0.0
    total_value_at_sea: float = 0.0
    vessels_in_risk_zones: int = 0
    active_vessels: int = 0


class ExposureByRegion(BaseModel):
    """Cargo exposure aggregated by discharge region."""

    region: str
    total_tons: float
    total_value: float
    shipment_count: int
