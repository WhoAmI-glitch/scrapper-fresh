"""Google Calendar API integration.

Provides calendar event fetching, webhook registration, and
meeting detection from calendar events.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    logger.warning("Google API libraries not available. Calendar sync disabled.")


SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events.readonly",
]

TRADING_KEYWORDS = [
    "charcoal", "shipment", "trading", "vessel", "cargo",
    "deal", "contract", "review", "weekly", "monthly",
    "buyer", "seller", "broker", "logistics", "freight",
]


class GoogleCalendarClient:
    """Client for Google Calendar API v3."""

    def __init__(self, credentials_path: str, token_path: str):
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)
        self._service = None

    def _get_credentials(self) -> "Credentials | None":
        """Load or create Google OAuth2 credentials."""
        if not GOOGLE_AVAILABLE:
            return None

        creds = None
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            self.token_path.write_text(creds.to_json())
        elif not creds or not creds.valid:
            if not self.credentials_path.exists():
                logger.warning("Google credentials file not found: {}", self.credentials_path)
                return None
            flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)
            self.token_path.write_text(creds.to_json())

        return creds

    def _get_service(self):
        """Get or create the Calendar API service."""
        if self._service is None:
            creds = self._get_credentials()
            if creds is None:
                return None
            self._service = build("calendar", "v3", credentials=creds)
        return self._service

    def get_upcoming_events(self, max_results: int = 50) -> list[dict]:
        """Fetch upcoming calendar events."""
        service = self._get_service()
        if service is None:
            return []

        now = datetime.now(timezone.utc).isoformat()
        try:
            result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=now,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            return result.get("items", [])
        except Exception as e:
            logger.error("Failed to fetch calendar events: {}", e)
            return []

    def get_events_since(self, updated_min: str, max_results: int = 50) -> list[dict]:
        """Fetch events updated since a given timestamp."""
        service = self._get_service()
        if service is None:
            return []

        try:
            result = (
                service.events()
                .list(
                    calendarId="primary",
                    updatedMin=updated_min,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            return result.get("items", [])
        except Exception as e:
            logger.error("Failed to fetch calendar events: {}", e)
            return []

    @staticmethod
    def is_trading_meeting(event: dict) -> bool:
        """Check if a calendar event is likely a trading meeting."""
        title = (event.get("summary") or "").lower()
        description = (event.get("description") or "").lower()
        text = f"{title} {description}"

        # Has Google Meet link
        has_meet = bool(event.get("hangoutLink") or event.get("conferenceData"))

        # Contains trading keywords
        keyword_match = any(kw in text for kw in TRADING_KEYWORDS)

        return has_meet and keyword_match

    @staticmethod
    def extract_meet_url(event: dict) -> str | None:
        """Extract Google Meet URL from a calendar event."""
        if event.get("hangoutLink"):
            return event["hangoutLink"]
        conf = event.get("conferenceData", {})
        for entry in conf.get("entryPoints", []):
            if entry.get("entryPointType") == "video":
                return entry.get("uri")
        return None

    @staticmethod
    def extract_attendees(event: dict) -> list[dict]:
        """Extract attendee list from a calendar event."""
        attendees = []
        for att in event.get("attendees", []):
            attendees.append({
                "email": att.get("email", ""),
                "name": att.get("displayName", att.get("email", "")),
                "organizer": att.get("organizer", False),
                "response_status": att.get("responseStatus", "needsAction"),
            })
        return attendees
