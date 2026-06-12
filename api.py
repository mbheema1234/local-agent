"""
FastAPI HTTP server that wraps the agent loop.
The Swift UI (and anything else) talks to this over HTTP.

Run: python api.py [--host 0.0.0.0] [--port 8765]
     (0.0.0.0 to allow iPhone on same Wi-Fi to connect)
"""
import argparse
import asyncio
import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from pydantic import BaseModel

load_dotenv(Path(__file__).parent / ".env")

ROOT = Path(__file__).parent
VENV_PYTHON = ROOT / "agent" / "bin" / "python3"
SERVER_SCRIPT = ROOT / "mcp_server.py"
MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-6")

SYSTEM_PROMPT = (
    "You are a personal assistant with access to Gmail, Google Calendar, LinkedIn, "
    "and web search. Be concise and helpful. When searching emails or calendar, "
    "summarize key points rather than dumping raw data."
)

# App-lifetime state stored on app.state in lifespan
_ai_client: Optional[AsyncOpenAI] = None
_mcp_session = None
_openai_tools: list = []
_tool_names: list[str] = []


def _mcp_tool_to_openai(tool) -> dict:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.inputSchema,
        },
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _ai_client, _mcp_session, _openai_tools, _tool_names

    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    python_bin = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    server_params = StdioServerParameters(
        command=python_bin,
        args=[str(SERVER_SCRIPT)],
        env=dict(os.environ),
    )

    _ai_client = AsyncOpenAI(
        api_key=os.getenv("OPENROUTER_KEY", ""),
        base_url="https://openrouter.ai/api/v1",
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            _mcp_session = session
            tools_result = await session.list_tools()
            _openai_tools = [_mcp_tool_to_openai(t) for t in tools_result.tools]
            _tool_names = [t.name for t in tools_result.tools]
            print(f"[api] MCP server connected — {len(_openai_tools)} tools loaded")
            yield


app = FastAPI(title="Local Agent API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ────────────────────────────────────────────────

class HistoryMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[HistoryMessage] = []


class ToolCallRecord(BaseModel):
    name: str
    arguments: str  # formatted as "key=val, key=val"
    result: str


class ChatResponse(BaseModel):
    response: str
    tool_calls: list[ToolCallRecord] = []


class HealthResponse(BaseModel):
    status: str
    model: str
    tools: list[str]


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", model=MODEL, tools=_tool_names)


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if _mcp_session is None:
        raise HTTPException(status_code=503, detail="MCP session not ready")
    if not _ai_client.api_key or _ai_client.api_key == "sk-or-v1-...":
        raise HTTPException(status_code=503, detail="OPENROUTER_KEY not configured")

    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in req.history:
        messages.append({"role": h.role, "content": h.content})
    messages.append({"role": "user", "content": req.message})

    tool_records: list[ToolCallRecord] = []

    while True:
        response = await _ai_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=_openai_tools,
            tool_choice="auto",
        )

        choice = response.choices[0]
        msg = choice.message

        assistant_msg: dict = {"role": "assistant", "content": msg.content or ""}
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
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                try:
                    result = await _mcp_session.call_tool(tc.function.name, args)
                    tool_content = "\n".join(
                        c.text for c in result.content if hasattr(c, "text")
                    )
                except Exception as e:
                    tool_content = f"Error: {e}"

                tool_records.append(
                    ToolCallRecord(
                        name=tc.function.name,
                        arguments=", ".join(f"{k}={v!r}" for k, v in args.items()),
                        result=tool_content,
                    )
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": tool_content,
                    }
                )
        else:
            return ChatResponse(
                response=msg.content or "",
                tool_calls=tool_records,
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (use 0.0.0.0 for network access from iPhone)")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    print(f"[api] Starting on http://{args.host}:{args.port}")
    uvicorn.run("api:app", host=args.host, port=args.port, reload=False)
