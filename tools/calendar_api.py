from datetime import datetime, timedelta, timezone

from googleapiclient.discovery import build

from .gmail import get_credentials


def list_events(days_ahead: int = 7, max_results: int = 20) -> str:
    """List upcoming calendar events for the next N days."""
    service = build("calendar", "v3", credentials=get_credentials())
    now = datetime.now(timezone.utc)
    time_max = now + timedelta(days=days_ahead)

    events_result = service.events().list(
        calendarId="primary",
        timeMin=now.isoformat(),
        timeMax=time_max.isoformat(),
        maxResults=max_results,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = events_result.get("items", [])
    if not events:
        return f"No events in the next {days_ahead} days."

    lines = []
    for e in events:
        start = e["start"].get("dateTime", e["start"].get("date", ""))
        summary = e.get("summary", "(no title)")
        location = e.get("location", "")
        loc_str = f" @ {location}" if location else ""
        lines.append(f"{start}: {summary}{loc_str}")

    return "\n".join(lines)


def search_events(query: str, days_ahead: int = 30, max_results: int = 10) -> str:
    """Search calendar events by keyword."""
    service = build("calendar", "v3", credentials=get_credentials())
    now = datetime.now(timezone.utc)
    time_max = now + timedelta(days=days_ahead)

    events_result = service.events().list(
        calendarId="primary",
        timeMin=now.isoformat(),
        timeMax=time_max.isoformat(),
        maxResults=max_results,
        singleEvents=True,
        orderBy="startTime",
        q=query,
    ).execute()

    events = events_result.get("items", [])
    if not events:
        return f"No events matching '{query}'."

    lines = []
    for e in events:
        start = e["start"].get("dateTime", e["start"].get("date", ""))
        summary = e.get("summary", "(no title)")
        description = e.get("description", "")[:200]
        desc_str = f"\n  {description}" if description else ""
        lines.append(f"{start}: {summary}{desc_str}")

    return "\n".join(lines)
