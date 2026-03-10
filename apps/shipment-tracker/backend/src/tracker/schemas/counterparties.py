"""Pydantic schemas for Counterparty endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


CounterpartyType = Literal["buyer", "seller", "broker", "agent"]


class CounterpartyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    short_name: str | None = Field(default=None, max_length=50)
    type: CounterpartyType = "buyer"
    country: str | None = Field(default=None, max_length=100)
    tax_id: str | None = Field(default=None, max_length=50)
    primary_contact_name: str | None = Field(default=None, max_length=200)
    primary_contact_email: str | None = Field(default=None, max_length=200)
    primary_contact_phone: str | None = Field(default=None, max_length=50)
    notes: str | None = None


class CounterpartyUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=300)
    short_name: str | None = Field(default=None, max_length=50)
    type: CounterpartyType | None = None
    country: str | None = Field(default=None, max_length=100)
    tax_id: str | None = Field(default=None, max_length=50)
    primary_contact_name: str | None = Field(default=None, max_length=200)
    primary_contact_email: str | None = Field(default=None, max_length=200)
    primary_contact_phone: str | None = Field(default=None, max_length=50)
    notes: str | None = None


class CounterpartyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    short_name: str | None = None
    type: CounterpartyType
    country: str | None = None
    tax_id: str | None = None
    primary_contact_name: str | None = None
    primary_contact_email: str | None = None
    primary_contact_phone: str | None = None
    notes: str | None = None
    deal_count: int = 0
    created_at: datetime
    updated_at: datetime


class CounterpartyListResponse(BaseModel):
    items: list[CounterpartyResponse]
    total: int
    page: int
    page_size: int
