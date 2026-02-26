#!/usr/bin/env python3
"""
n8n-claude-server: FastAPI server to bridge n8n webhooks to Claude Code CLI
"""

import os
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="n8n Claude Server")

# Claude Code CLI path
CLAUDE_BIN = "/Users/ethan/Library/pnpm/claude"

# Working directory for Claude
WORK_DIR = "/Users/ethan/Projects"


class ClaudeRequest(BaseModel):
    prompt: str
    project_path: Optional[str] = None
    model: Optional[str] = None


class ClaudeResponse(BaseModel):
    success: bool
    output: str
    error: Optional[str] = None


def run_claude(prompt: str, project_path: Optional[str] = None) -> tuple[str, str]:
    """Run Claude CLI with the given prompt"""
    work_dir = project_path if project_path else WORK_DIR

    # Build the command - Claude Code uses --print flag for non-interactive output
    cmd = [CLAUDE_BIN, "--print", "-p", prompt]

    # Remove CLAUDECODE env var to allow running from within Claude session
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)

    try:
        result = subprocess.run(
            cmd,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
            env=env
        )
        return result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return "", "Timeout: Claude took too long to respond"
    except Exception as e:
        return "", str(e)


@app.post("/claude", response_model=ClaudeResponse)
async def claude_endpoint(request: ClaudeRequest, background_tasks: BackgroundTasks):
    """Execute Claude Code with a prompt"""
    stdout, stderr = run_claude(request.prompt, request.project_path)

    if stderr and not stdout:
        return ClaudeResponse(success=False, output="", error=stderr)

    return ClaudeResponse(success=True, output=stdout, error=stderr if stderr else None)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
