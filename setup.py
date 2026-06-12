"""
One-time setup: installs dependencies, runs Google OAuth, and saves LinkedIn session.
Run this before using the agent for the first time.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
VENV_PYTHON = ROOT / "agent" / "bin" / "python3"
VENV_PIP = ROOT / "agent" / "bin" / "pip"

python = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
pip = str(VENV_PIP) if VENV_PIP.exists() else f"{python} -m pip"


def run(cmd: list[str], **kwargs):
    print(f"  $ {' '.join(cmd)}")
    subprocess.run(cmd, check=True, **kwargs)


def step(msg: str):
    print(f"\n{'─'*60}\n  {msg}\n{'─'*60}")


def main():
    print("\n=== Local Agent Setup ===\n")

    # 1. Install Python deps
    step("Step 1/4 — Installing Python dependencies")
    run([python, "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")])

    # 2. Install Playwright browsers
    step("Step 2/4 — Installing Playwright Chromium browser")
    run([python, "-m", "playwright", "install", "chromium"])

    # 3. Create .env if missing
    step("Step 3/4 — Setting up .env")
    env_file = ROOT / ".env"
    if not env_file.exists():
        env_example = ROOT / ".env.example"
        env_file.write_text(env_example.read_text())
        print(f"  Created .env from .env.example")
        print(f"  !! Edit {env_file} and fill in OPENROUTER_KEY and LINKEDIN credentials before continuing.")
        return
    else:
        print(f"  .env already exists — skipping.")

    from dotenv import load_dotenv
    load_dotenv(env_file)

    # 4. Google OAuth
    step("Step 4/4 — Google OAuth (Gmail + Calendar)")
    creds_file = ROOT / "google_credentials.json"
    token_file = ROOT / "google_token.json"

    if not creds_file.exists():
        print("""
  To enable Gmail and Calendar access:

  1. Go to https://console.cloud.google.com/
  2. Create a new project (or select an existing one)
  3. Enable APIs: search for "Gmail API" and "Google Calendar API" and enable both
  4. Go to "APIs & Services" > "Credentials"
  5. Click "Create Credentials" > "OAuth 2.0 Client IDs"
  6. Application type: Desktop app
  7. Download the JSON file and save it as:
       """ + str(creds_file) + """

  Then re-run: python setup.py
""")
        return

    if not token_file.exists():
        print("  Opening browser for Google OAuth flow...")
        sys.path.insert(0, str(ROOT))
        from tools.gmail import get_credentials
        get_credentials()
        print("  Google auth saved.")
    else:
        print("  Google token already exists — skipping.")

    # 5. LinkedIn session
    session_file = ROOT / "linkedin_session.json"
    if not session_file.exists():
        import os
        li_email = os.getenv("LINKEDIN_EMAIL", "")
        li_pass = os.getenv("LINKEDIN_PASSWORD", "")
        if li_email and li_pass and li_email != "your@email.com":
            print("\n  Logging into LinkedIn (browser will open briefly)...")
            sys.path.insert(0, str(ROOT))
            import asyncio
            from tools.linkedin import _get_page
            async def _login():
                pw, browser, context, page = await _get_page()
                await browser.close()
                await pw.stop()
            asyncio.run(_login())
            print("  LinkedIn session saved.")
        else:
            print("\n  Skipping LinkedIn login — set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env first.")
    else:
        print("  LinkedIn session already exists — skipping.")

    print("\n=== Setup complete! Run the agent with: ===")
    print(f"  {python} agent.py            # CLI only")
    print(f"  {python} agent.py --daemon   # CLI + background scheduled tasks")
    print(f"  {python} mcp_server.py       # MCP server only (for Claude Desktop etc.)\n")


if __name__ == "__main__":
    main()
