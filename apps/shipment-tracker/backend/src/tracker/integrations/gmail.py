"""Gmail API integration for fetching shipment-related emails.

Uses Google's official API client with OAuth2 credentials. The initial
authentication flow requires a browser; subsequent runs use a cached
refresh token stored at TRACKER_GMAIL_TOKEN_PATH.
"""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger


class GmailClient:
    """Async-compatible wrapper around the Gmail API.

    Although google-api-python-client is synchronous, we wrap calls
    to keep the interface consistent with the rest of the async codebase.
    Actual API calls are fast enough (network-bound) that blocking is
    acceptable in the worker context.
    """

    def __init__(self) -> None:
        self._service: Any = None
        self._user_id: str = "me"

    def connect(self, credentials_path: str, token_path: str) -> None:
        """Authenticate with Gmail API using OAuth2 credentials.

        On first run, opens a browser for user consent. On subsequent
        runs, uses the cached token at token_path.

        Args:
            credentials_path: Path to the OAuth2 client credentials JSON.
            token_path: Path to store/load the refresh token.
        """
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
        except ImportError as exc:
            logger.error(
                "Gmail integration requires google-api-python-client and "
                "google-auth-oauthlib. Install with: pip install "
                "google-api-python-client google-auth-oauthlib"
            )
            raise exc

        scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
        creds: Credentials | None = None

        token_file = Path(token_path)
        if token_file.exists():
            creds = Credentials.from_authorized_user_file(str(token_file), scopes)

        if creds is None or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired Gmail token")
                creds.refresh(Request())
            else:
                logger.info("Starting Gmail OAuth2 flow (browser required)")
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, scopes
                )
                creds = flow.run_local_server(port=0)

            token_file.write_text(creds.to_json())
            logger.info("Gmail token saved to {}", token_path)

        self._service = build("gmail", "v1", credentials=creds)
        logger.info("Gmail API connected successfully")

    def is_connected(self) -> bool:
        """Check if the Gmail client has been authenticated."""
        return self._service is not None

    def fetch_new_messages(
        self,
        after_timestamp: datetime | None = None,
        query_filter: str = "",
        max_results: int = 50,
    ) -> list[dict[str, Any]]:
        """Fetch message IDs matching the filter since the given timestamp.

        Args:
            after_timestamp: Only fetch messages received after this time.
            query_filter: Gmail search query string.
            max_results: Maximum number of messages to return.

        Returns:
            List of dicts with 'id' and 'threadId' keys.
        """
        if self._service is None:
            logger.warning("Gmail client not connected, returning empty list")
            return []

        query_parts: list[str] = []
        if query_filter:
            query_parts.append(query_filter)
        if after_timestamp:
            # Gmail query uses epoch seconds for after: filter
            epoch = int(after_timestamp.timestamp())
            query_parts.append(f"after:{epoch}")

        query = " ".join(query_parts) if query_parts else None

        try:
            result = (
                self._service.users()
                .messages()
                .list(userId=self._user_id, q=query, maxResults=max_results)
                .execute()
            )
            messages = result.get("messages", [])
            logger.debug("Fetched {} message IDs from Gmail", len(messages))
            return messages
        except Exception as exc:
            logger.error("Failed to fetch Gmail messages: {}", exc)
            return []

    def get_message_detail(self, message_id: str) -> dict[str, Any]:
        """Fetch full message details including body and attachment metadata.

        Returns a normalized dict with:
        - id: Gmail message ID
        - subject: email subject
        - sender: From address
        - recipients: list of To addresses
        - body_text: plain text body
        - received_at: datetime of receipt
        - attachments: list of {id, filename, size} dicts
        """
        if self._service is None:
            raise RuntimeError("Gmail client not connected")

        try:
            msg = (
                self._service.users()
                .messages()
                .get(userId=self._user_id, id=message_id, format="full")
                .execute()
            )
        except Exception as exc:
            logger.error("Failed to fetch message {}: {}", message_id, exc)
            raise

        headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}

        # Extract plain text body
        body_text = _extract_body_text(msg.get("payload", {}))

        # Extract attachment metadata
        attachments = _extract_attachments(msg.get("payload", {}), message_id)

        # Parse internal date (milliseconds since epoch)
        internal_date_ms = int(msg.get("internalDate", 0))
        received_at = datetime.fromtimestamp(
            internal_date_ms / 1000.0, tz=timezone.utc
        )

        # Parse recipients
        to_header = headers.get("to", "")
        recipients = [addr.strip() for addr in to_header.split(",") if addr.strip()]

        return {
            "id": message_id,
            "subject": headers.get("subject", "(no subject)"),
            "sender": headers.get("from", ""),
            "recipients": recipients,
            "body_text": body_text,
            "received_at": received_at,
            "attachments": attachments,
        }

    def download_attachment(
        self, message_id: str, attachment_id: str
    ) -> bytes:
        """Download an attachment by its Gmail attachment ID.

        Returns the raw file bytes.
        """
        if self._service is None:
            raise RuntimeError("Gmail client not connected")

        try:
            result = (
                self._service.users()
                .messages()
                .attachments()
                .get(userId=self._user_id, messageId=message_id, id=attachment_id)
                .execute()
            )
            data = result.get("data", "")
            # Gmail API returns URL-safe base64
            return base64.urlsafe_b64decode(data)
        except Exception as exc:
            logger.error(
                "Failed to download attachment {} from message {}: {}",
                attachment_id,
                message_id,
                exc,
            )
            raise


def _extract_body_text(payload: dict[str, Any]) -> str:
    """Recursively extract plain text from a Gmail message payload.

    Handles both simple and multipart MIME structures.
    """
    mime_type = payload.get("mimeType", "")

    # Direct plain text body
    if mime_type == "text/plain":
        body_data = payload.get("body", {}).get("data", "")
        if body_data:
            return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")

    # Multipart: recurse into parts
    parts = payload.get("parts", [])
    for part in parts:
        result = _extract_body_text(part)
        if result:
            return result

    return ""


def _extract_attachments(
    payload: dict[str, Any], message_id: str
) -> list[dict[str, Any]]:
    """Extract attachment metadata from a Gmail message payload."""
    attachments: list[dict[str, Any]] = []

    def _recurse(part: dict[str, Any]) -> None:
        filename = part.get("filename")
        body = part.get("body", {})
        attachment_id = body.get("attachmentId")

        if filename and attachment_id:
            attachments.append(
                {
                    "id": attachment_id,
                    "message_id": message_id,
                    "filename": filename,
                    "size": body.get("size", 0),
                    "mime_type": part.get("mimeType", "application/octet-stream"),
                }
            )

        for sub_part in part.get("parts", []):
            _recurse(sub_part)

    _recurse(payload)
    return attachments


def create_gmail_client() -> GmailClient:
    """Factory that creates an unauthenticated GmailClient instance.

    Call .connect() on the returned client to authenticate.
    """
    return GmailClient()
