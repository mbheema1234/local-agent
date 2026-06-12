"""
MCP server exposing Gmail, LinkedIn, Calendar, and web search tools.
Run directly or connect via Claude Desktop / a custom agent.
"""
import sys
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(Path(__file__).parent / ".env")

mcp = FastMCP("local-agent")


# ── Gmail ────────────────────────────────────────────────────────────────────

@mcp.tool()
def search_emails(query: str, max_results: int = 10) -> str:
    """Search Gmail using the same query syntax as the Gmail search bar (e.g. 'from:boss@company.com subject:urgent')."""
    from tools.gmail import search_emails as _fn
    return _fn(query, max_results)


@mcp.tool()
def read_email(message_id: str) -> str:
    """Read the full content of an email. Use message IDs returned by search_emails."""
    from tools.gmail import read_email as _fn
    return _fn(message_id)


@mcp.tool()
def list_recent_emails(max_results: int = 20) -> str:
    """List the most recent emails in the inbox."""
    from tools.gmail import list_recent_emails as _fn
    return _fn(max_results)


# ── Google Calendar ───────────────────────────────────────────────────────────

@mcp.tool()
def list_calendar_events(days_ahead: int = 7, max_results: int = 20) -> str:
    """List upcoming Google Calendar events for the next N days."""
    from tools.calendar_api import list_events as _fn
    return _fn(days_ahead, max_results)


@mcp.tool()
def search_calendar_events(query: str, days_ahead: int = 30, max_results: int = 10) -> str:
    """Search upcoming calendar events by keyword."""
    from tools.calendar_api import search_events as _fn
    return _fn(query, days_ahead, max_results)


# ── Web Search ────────────────────────────────────────────────────────────────

@mcp.tool()
def search_web(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo and return titles, URLs, and summaries."""
    from tools.search import search_web as _fn
    return _fn(query, max_results)


# ── LinkedIn ──────────────────────────────────────────────────────────────────

@mcp.tool()
def search_linkedin_people(query: str, max_results: int = 5) -> str:
    """Search LinkedIn for people by name, job title, or keyword."""
    from tools.linkedin import search_linkedin_people as _fn
    return _fn(query, max_results)


@mcp.tool()
def search_linkedin_jobs(query: str, location: str = "", max_results: int = 5) -> str:
    """Search LinkedIn job postings by keyword and optional location."""
    from tools.linkedin import search_linkedin_jobs as _fn
    return _fn(query, location, max_results)


@mcp.tool()
def get_linkedin_profile(profile_url_or_slug: str) -> str:
    """Get details from a LinkedIn profile. Pass a full URL or just the username slug (e.g. 'john-doe-123')."""
    from tools.linkedin import get_linkedin_profile as _fn
    return _fn(profile_url_or_slug)


if __name__ == "__main__":
    mcp.run()
