"""Single-user, bearer-authenticated MCP HTTP gateway for DesignCraft stdio.

Only one DesignCraft session and one request at a time. The gateway is intentionally
not a multi-tenant service. Railway / Render single-replica deployment only.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os
from pathlib import Path
import re
import shutil
import time
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response

LOG = logging.getLogger("designcraft.gateway")
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("MCP_BEARER_TOKEN", "")
if len(TOKEN) < 24:
    raise RuntimeError("Set MCP_BEARER_TOKEN to a random secret of at least 24 characters")

BASE = Path(os.getenv("WORKSPACE_DIR", "/workspace")).resolve()
INPUT = BASE / "inputs"
OUTPUT = BASE / "output"
INPUT.mkdir(parents=True, exist_ok=True)
OUTPUT.mkdir(parents=True, exist_ok=True)
CLI = os.getenv("DESIGNCRAFT_CLI", "designcraft-cli")
TIMEOUT = min(max(int(os.getenv("MCP_TOOL_TIMEOUT", "180")), 10), 600)
MAX_BYTES = 32 * 1024 * 1024
MAX_UPLOAD = 14 * 1024 * 1024
NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
ALLOWED = {".png", ".jpg", ".jpeg", ".webp", ".pdf", ".csv", ".tsv", ".xlsx"}
EXPORTS = {".pdf", ".png", ".jpg", ".jpeg", ".epub", ".designcraft", ".idml", ".txt", ".html"}

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


def is_authorized(header: str | None) -> bool:
    if not header or not header.startswith("Bearer "):
        return False
    return hmac.compare_digest(header[7:], TOKEN)


def check_auth(request: Request):
    if not is_authorized(request.headers.get("authorization")):
        raise HTTPException(status_code=401, detail="Unauthorized", headers={"WWW-Authenticate": "Bearer"})


def safe_path(folder: Path, filename: str, extensions: set[str]) -> Path:
    if not NAME.fullmatch(filename) or filename in (".", ".."):
        raise HTTPException(status_code=400, detail="Invalid filename")
    if Path(filename).suffix.lower() not in extensions:
        raise HTTPException(status_code=400, detail="Unsupported extension")
    target = (folder / filename).resolve()
    if target.parent != folder.resolve():
        raise HTTPException(status_code=400, detail="Invalid path")
    return target


def tool_ok(payload: str) -> dict:
    return {"content": [{"type": "text", "text": payload}]}


def tool_error(payload: str) -> dict:
    return {"content": [{"type": "text", "text": payload}], "isError": True}


def extra_tools() -> list[dict]:
    return [
        {"name": "gateway_save_asset", "description": "Write a base64-encoded source asset to the DesignCraft inputs directory (up to 14 MB).", "inputSchema": {"type": "object", "properties": {"filename": {"type": "string"}, "base64_data": {"type": "string"}}, "required": ["filename", "base64_data"]}},
        {"name": "gateway_list_outputs", "description": "List the saved exports in the output directory.", "inputSchema": {"type": "object", "properties": {}}},
        {"name": "gateway_get_download_link", "description": "Create a 20-minute signed download URL for a saved DesignCraft export.", "inputSchema": {"type": "object", "properties": {"filename": {"type": "string"}}, "required": ["filename"]}},
    ]


def signed_link(filename: str, request: Request) -> str:
    expire = int(time.time()) + 1200
    message = f"{filename}:{expire}".encode()
    sig = hmac.new(TOKEN.encode(), message, hashlib.sha256).hexdigest()
    base_url = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
    if not base_url:
        base_url = str(request.base_url).rstrip("/")
    return f"{base_url}/download/{quote(filename)}?expires={expire}&signature={sig}"


class ProcessBridge:
    def __init__(self):
        self.proc: asyncio.subprocess.Process | None = None
        self.lock = asyncio.Lock()
        self.stderr_task: asyncio.Task | None = None
        self.serial = 0

    async def start(self):
        if self.proc and self.proc.returncode is None:
            return
        binary = shutil.which(CLI) if "/" not in CLI else CLI
        if not binary:
            raise RuntimeError("DesignCraft CLI not installed")
        self.proc = await asyncio.create_subprocess_exec(
            binary, "mcp", "--automation-read-root", str(INPUT),
            "--automation-read-root", str(OUTPUT),
            "--automation-write-root", str(OUTPUT),
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE, cwd=str(BASE),
        )
        self.stderr_task = asyncio.create_task(self._drain_stderr())

    async def _drain_stderr(self):
        assert self.proc and self.proc.stderr
        while line := await self.proc.stderr.readline():
            LOG.info("designcraft: %s", line.decode("utf-8", errors="replace").rstrip()[:500])

    async def exchange(self, message: dict, expect_reply: bool = True):
        async with self.lock:
            await self.start()
            assert self.proc and self.proc.stdin and self.proc.stdout
            data = (json.dumps(message, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
            if len(data) > MAX_BYTES:
                raise HTTPException(status_code=413, detail="MCP request too large")
            self.proc.stdin.write(data)
            await self.proc.stdin.drain()
            if not expect_reply:
                return None
            goal = message.get("id")
            try:
                while True:
                    line = await asyncio.wait_for(self.proc.stdout.readline(), timeout=TIMEOUT)
                    if not line:
                        raise RuntimeError("DesignCraft closed stdout")
                    if len(line) > 64 * 1024 * 1024:
                        raise RuntimeError("DesignCraft response too large")
                    answer = json.loads(line)
                    if answer.get("id") == goal:
                        return answer
                    LOG.info("Ignoring unsolicited upstream MCP message")
            except (asyncio.TimeoutError, RuntimeError, json.JSONDecodeError):
                if self.proc.returncode is None:
                    self.proc.kill()
                    await self.proc.wait()
                self.proc = None
                raise


bridge = ProcessBridge()


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "designcraft_cli_installed": bool(shutil.which(CLI))}


@app.post("/mcp")
async def mcp(request: Request):
    check_auth(request)
    payload = await request.body()
    if len(payload) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Request too large")
    try:
        obj = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    if not isinstance(obj, dict) or obj.get("jsonrpc") != "2.0" or not isinstance(obj.get("method"), str):
        raise HTTPException(status_code=400, detail="Invalid JSON-RPC request")
    method = obj["method"]
    if method not in {"initialize", "notifications/initialized", "ping", "tools/list", "tools/call"}:
        return JSONResponse({"jsonrpc": "2.0", "id": obj.get("id"), "error": {"code": -32601, "message": "Method not allowed"}})
    request_id = obj.get("id")
    if method == "tools/call":
        params = obj.get("params") or {}
        if not isinstance(params, dict):
            raise HTTPException(status_code=400, detail="Invalid tools/call params")
        name = params.get("name")
        args = params.get("arguments") or {}
        if not isinstance(args, dict):
            raise HTTPException(status_code=400, detail="Invalid tool arguments")
        if name in {"gateway_save_asset", "gateway_list_outputs", "gateway_get_download_link"}:
            result = await gateway_tool(name, args, request)
            return JSONResponse({"jsonrpc": "2.0", "id": request_id, "result": result})
    try:
        answer = await bridge.exchange(obj, expect_reply=(request_id is not None))
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="DesignCraft timeout")
    except Exception as exc:
        LOG.exception("DesignCraft request failed: %s", type(exc).__name__)
        raise HTTPException(status_code=502, detail="DesignCraft unavailable")
    if answer is None:
        return Response(status_code=202)
    if method == "tools/list" and "result" in answer and isinstance(answer["result"], dict):
        answer["result"].setdefault("tools", []).extend(extra_tools())
    return JSONResponse(answer, headers={"Cache-Control": "no-store"})


async def gateway_tool(name: str, args: dict, request: Request) -> dict:
    if name == "gateway_save_asset":
        try:
            p = safe_path(INPUT, args["filename"], ALLOWED)
            raw = base64.b64decode(args["base64_data"], validate=True)
            if not raw or len(raw) > MAX_UPLOAD:
                return tool_error("Asset size must be between 1 byte and 14 MB")
            # Require PDF/image signatures where feasible, refuse executable masquerading as image.
            suffix = p.suffix.lower()
            if suffix == ".pdf" and not raw.startswith(b"%PDF-"):
                return tool_error("Invalid PDF signature")
            if suffix == ".png" and not raw.startswith(b"\x89PNG\r\n\x1a\n"):
                return tool_error("Invalid PNG signature")
            if suffix in (".jpg", ".jpeg") and not raw.startswith(b"\xff\xd8\xff"):
                return tool_error("Invalid JPEG signature")
            tmp = p.with_suffix(p.suffix + ".tmp")
            tmp.write_bytes(raw)
            tmp.replace(p)
            return tool_ok(f"Asset saved: {p} ({len(raw)} bytes)")
        except (ValueError, KeyError, TypeError, OSError, HTTPException) as exc:
            return tool_error(f"Asset not saved: {type(exc).__name__}")
    if name == "gateway_list_outputs":
        rows = [{"filename": p.name, "size_bytes": p.stat().st_size} for p in sorted(OUTPUT.iterdir()) if p.is_file() and p.suffix.lower() in EXPORTS and not p.is_symlink()]
        return tool_ok(json.dumps(rows, ensure_ascii=False))
    if name == "gateway_get_download_link":
        try:
            p = safe_path(OUTPUT, args["filename"], EXPORTS)
            if not p.is_file() or p.is_symlink():
                return tool_error("Export does not exist")
            return tool_ok(signed_link(p.name, request))
        except (KeyError, HTTPException):
            return tool_error("Invalid export filename")
    return tool_error("Unknown gateway tool")


@app.get("/download/{filename}")
async def download(filename: str, request: Request, expires: int, signature: str):
    if abs(expires - int(time.time())) > 1200 or expires < int(time.time()):
        raise HTTPException(status_code=403, detail="Expired URL")
    try:
        p = safe_path(OUTPUT, filename, EXPORTS)
    except HTTPException:
        raise HTTPException(status_code=404, detail="Not found")
    expected = hmac.new(TOKEN.encode(), f"{filename}:{expires}".encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected) or not p.is_file() or p.is_symlink():
        raise HTTPException(status_code=403, detail="Invalid link")
    return FileResponse(p, filename=filename, headers={"Cache-Control": "private, no-store"})