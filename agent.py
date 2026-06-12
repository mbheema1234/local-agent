"""
CLI agent that connects to the local MCP server and uses OpenRouter for inference.
Supports interactive chat and an optional background daemon for scheduled tasks.
"""
import asyncio
import json
import os
import sys
import threading
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt

load_dotenv(Path(__file__).parent / ".env")

console = Console()

OPENROUTER_KEY = os.getenv("OPENROUTER_KEY", "")
MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-6")
VENV_PYTHON = Path(__file__).parent / "agent" / "bin" / "python3"
SERVER_SCRIPT = Path(__file__).parent / "mcp_server.py"

SYSTEM_PROMPT = (
    "You are a personal assistant with access to Gmail, Google Calendar, LinkedIn, "
    "and web search. Be concise and helpful. When searching emails or calendar, "
    "always summarize the key points rather than dumping raw data."
)


def _mcp_tool_to_openai(tool) -> dict:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.inputSchema,
        },
    }


async def run_agent(with_daemon: bool = False):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    if not OPENROUTER_KEY or OPENROUTER_KEY == "sk-or-v1-...":
        console.print("[red]Error:[/red] Set OPENROUTER_KEY in your .env file.")
        sys.exit(1)

    python_bin = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    server_params = StdioServerParameters(
        command=python_bin,
        args=[str(SERVER_SCRIPT)],
        env={**os.environ},
    )

    client = AsyncOpenAI(
        api_key=OPENROUTER_KEY,
        base_url="https://openrouter.ai/api/v1",
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            openai_tools = [_mcp_tool_to_openai(t) for t in tools_result.tools]

            if with_daemon:
                _start_daemon_thread(session)

            console.print(
                f"[bold green]Agent ready[/bold green] — model: [cyan]{MODEL}[/cyan], "
                f"tools: [cyan]{len(openai_tools)}[/cyan]. Type [bold]exit[/bold] to quit.\n"
            )

            messages = [{"role": "system", "content": SYSTEM_PROMPT}]

            while True:
                try:
                    user_input = Prompt.ask("[bold blue]You[/bold blue]").strip()
                except (EOFError, KeyboardInterrupt):
                    console.print("\n[dim]Goodbye.[/dim]")
                    break

                if user_input.lower() in ("exit", "quit", "q"):
                    break
                if not user_input:
                    continue

                messages.append({"role": "user", "content": user_input})

                while True:
                    response = await client.chat.completions.create(
                        model=MODEL,
                        messages=messages,
                        tools=openai_tools,
                        tool_choice="auto",
                    )

                    choice = response.choices[0]
                    msg = choice.message

                    assistant_msg = {"role": "assistant", "content": msg.content or ""}
                    if msg.tool_calls:
                        assistant_msg["tool_calls"] = [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in msg.tool_calls
                        ]
                    messages.append(assistant_msg)

                    if choice.finish_reason == "tool_calls" and msg.tool_calls:
                        for tc in msg.tool_calls:
                            tool_name = tc.function.name
                            try:
                                args = json.loads(tc.function.arguments)
                            except json.JSONDecodeError:
                                args = {}

                            console.print(f"  [dim]→ {tool_name}({', '.join(f'{k}={v!r}' for k, v in args.items())})[/dim]")

                            try:
                                result = await session.call_tool(tool_name, args)
                                tool_content = "\n".join(
                                    c.text for c in result.content if hasattr(c, "text")
                                )
                            except Exception as e:
                                tool_content = f"Error calling {tool_name}: {e}"

                            messages.append({
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "content": tool_content,
                            })
                    else:
                        if msg.content:
                            console.print()
                            console.print(Markdown(msg.content))
                            console.print()
                        break


def _start_daemon_thread(session):
    """Start the background daemon scheduler in a separate thread."""
    import daemon as daemon_module
    t = threading.Thread(
        target=lambda: asyncio.run(daemon_module.run_daemon(session)),
        daemon=True,
    )
    t.start()
    console.print("[dim]Background daemon started.[/dim]")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Local AI agent with MCP tools")
    parser.add_argument("--daemon", action="store_true", help="Also run background scheduled tasks")
    args = parser.parse_args()

    asyncio.run(run_agent(with_daemon=args.daemon))
