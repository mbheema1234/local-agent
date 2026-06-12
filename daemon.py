"""
Background daemon: scheduled tasks that run while the agent is active.
Can also be run standalone: python daemon.py
"""
import asyncio
import os
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from rich.console import Console

load_dotenv(Path(__file__).parent / ".env")

console = Console()

EMAIL_INTERVAL = int(os.getenv("EMAIL_CHECK_INTERVAL_MINUTES", "5"))

_seen_email_ids: set[str] = set()


async def check_new_emails():
    """Poll for new unread emails and print a summary."""
    try:
        from tools.gmail import search_emails

        result = search_emails("in:inbox is:unread", max_results=5)
        if result == "No messages found.":
            return

        lines = result.split("\n\n")
        new_lines = []
        for block in lines:
            msg_id = ""
            for line in block.splitlines():
                if line.startswith("ID: "):
                    msg_id = line[4:].strip()
                    break
            if msg_id and msg_id not in _seen_email_ids:
                _seen_email_ids.add(msg_id)
                new_lines.append(block)

        if new_lines:
            console.print(f"\n[bold yellow][Daemon][/bold yellow] {len(new_lines)} new email(s):")
            for block in new_lines:
                console.print(f"  [dim]{block.splitlines()[1] if len(block.splitlines()) > 1 else block}[/dim]")
    except Exception as e:
        console.print(f"[dim][Daemon] Email check failed: {e}[/dim]")


async def morning_calendar_summary():
    """Print today's calendar events (runs at 8 AM)."""
    try:
        from tools.calendar_api import list_events

        result = list_events(days_ahead=1, max_results=10)
        console.print(f"\n[bold yellow][Daemon][/bold yellow] Today's calendar:\n{result}")
    except Exception as e:
        console.print(f"[dim][Daemon] Calendar summary failed: {e}[/dim]")


async def run_daemon(mcp_session=None):
    """Start the APScheduler background scheduler. Runs until cancelled."""
    scheduler = AsyncIOScheduler()

    scheduler.add_job(check_new_emails, "interval", minutes=EMAIL_INTERVAL, id="email_check")
    scheduler.add_job(morning_calendar_summary, "cron", hour=8, minute=0, id="calendar_morning")

    scheduler.start()
    console.print(f"[dim][Daemon] Scheduler running — email check every {EMAIL_INTERVAL}m, calendar at 8 AM.[/dim]")

    try:
        while True:
            await asyncio.sleep(60)
    except (asyncio.CancelledError, KeyboardInterrupt):
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(run_daemon())
