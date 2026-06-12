import base64
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]

_CREDS_FILE = Path(__file__).parent.parent / "google_credentials.json"
_TOKEN_FILE = Path(__file__).parent.parent / "google_token.json"


def get_credentials() -> Credentials:
    creds = None
    if _TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(_TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not _CREDS_FILE.exists():
                raise FileNotFoundError(
                    "google_credentials.json not found. Run python setup.py to configure Google OAuth."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(_CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        _TOKEN_FILE.write_text(creds.to_json())
    return creds


def _decode_body(payload: dict) -> str:
    body = ""
    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain" and "data" in part.get("body", {}):
                body += base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
            elif "parts" in part:
                body += _decode_body(part)
    elif "body" in payload and "data" in payload["body"]:
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
    return body


def search_emails(query: str, max_results: int = 10) -> str:
    """Search Gmail with a query string (same syntax as Gmail search bar)."""
    service = build("gmail", "v1", credentials=get_credentials())
    results = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()
    messages = results.get("messages", [])
    if not messages:
        return "No messages found."

    summaries = []
    for msg in messages[:max_results]:
        detail = service.users().messages().get(userId="me", id=msg["id"], format="metadata",
                                                metadataHeaders=["Subject", "From", "Date"]).execute()
        headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
        summaries.append(
            f"ID: {msg['id']}\n"
            f"From: {headers.get('From', 'unknown')}\n"
            f"Subject: {headers.get('Subject', '(no subject)')}\n"
            f"Date: {headers.get('Date', 'unknown')}"
        )
    return "\n\n".join(summaries)


def read_email(message_id: str) -> str:
    """Read the full content of an email by its message ID."""
    service = build("gmail", "v1", credentials=get_credentials())
    detail = service.users().messages().get(userId="me", id=message_id, format="full").execute()
    headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
    body = _decode_body(detail.get("payload", {}))
    return (
        f"From: {headers.get('From', 'unknown')}\n"
        f"Subject: {headers.get('Subject', '(no subject)')}\n"
        f"Date: {headers.get('Date', 'unknown')}\n"
        f"Snippet: {detail.get('snippet', '')}\n\n"
        f"Body:\n{body[:4000]}"
    )


def list_recent_emails(max_results: int = 20) -> str:
    """List the most recent emails in the inbox."""
    return search_emails("in:inbox", max_results=max_results)
