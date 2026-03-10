"""Pydantic schemas for Meeting endpoints."""

from __future__ import annotations

from datetime import datetime, date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


MeetingStatus = Literal["scheduled", "in_progress", "processing", "completed", "failed"]
ActionItemStatus = Literal["open", "in_progress", "done", "cancelled"]


class MeetingCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    scheduled_start: datetime
    scheduled_end: datetime | None = None
    google_calendar_event_id: str | None = None
    google_meet_url: str | None = None


class MeetingUpdate(BaseModel):
    title: str | None = None
    status: MeetingStatus | None = None
    actual_duration_seconds: int | None = None
    recording_url: str | None = None


class ParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    email: str | None = None
    role: str = "attendee"
    talk_time_seconds: int = 0
    sentiment_score: float | None = None


class TranscriptSegment(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    speaker_name: str
    speaker_email: str | None = None
    text: str
    start_ms: int
    end_ms: int
    confidence: float | None = None
    sentiment: str | None = None


class MeetingSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    summary_text: str
    decisions: list = []
    market_intelligence: list = []
    model_used: str
    generated_at: datetime


class ActionItemCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: str | None = None
    assignee_name: str | None = None
    assignee_email: str | None = None
    due_date: date | None = None
    deal_id: UUID | None = None
    meeting_id: UUID | None = None


class ActionItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    description: str | None = None
    assignee_name: str | None = None
    assignee_email: str | None = None
    due_date: date | None = None
    status: ActionItemStatus
    source: str = "manual"
    confidence: float | None = None
    meeting_id: UUID | None = None
    deal_id: UUID | None = None
    created_at: datetime
    completed_at: datetime | None = None


class AiDealUpdateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    meeting_id: UUID
    deal_id: UUID
    field_name: str
    old_value: str | None = None
    proposed_value: str
    confidence: float
    status: str
    created_at: datetime


class MeetingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    scheduled_start: datetime
    scheduled_end: datetime | None = None
    actual_duration_seconds: int | None = None
    google_calendar_event_id: str | None = None
    google_meet_url: str | None = None
    status: MeetingStatus
    recording_url: str | None = None
    participants: list[ParticipantResponse] = []
    summary: MeetingSummaryResponse | None = None
    action_items: list[ActionItemResponse] = []
    linked_deal_ids: list[str] = []
    created_at: datetime
    updated_at: datetime


class MeetingListResponse(BaseModel):
    items: list[MeetingResponse]
    total: int
    page: int
    page_size: int
