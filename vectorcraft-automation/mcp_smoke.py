#!/usr/bin/env python3
"""Run VectorCraft's *real* official MCP server in an isolated GitHub Actions runner.
Only a small, validated declarative drawing request is accepted; no arbitrary code.
"""
import json
import pathlib
import re
import subprocess
import sys
import time

request_path = pathlib.Path(sys.argv[1])
output = pathlib.Path(sys.argv[2]).resolve()
output.mkdir(parents=True, exist_ok=True)
request = json.loads(request_path.read_text(encoding="utf-8"))
shapes = request.get("shapes", [])
if not isinstance(shapes, list) or not (1 <= len(shapes) <= 40):
    raise ValueError("request.shapes must contain 1 to 40 shapes")

def check_shape(s):
    if not isinstance(s, dict) or s.get("shape") not in ("rectangle", "ellipse"):
        raise ValueError("Only rectangle or ellipse shapes are permitted")
    allowed = {"shape", "x", "y", "width", "height", "fill", "stroke", "strokeWidth"}
    if set(s) - allowed:
        raise ValueError("Unknown shape fields")
    for name in ("x", "y", "width", "height"):
        v = s.get(name)
        if not isinstance(v, (float, int)) or isinstance(v, bool) or not (0 <= v <= 792):
            raise ValueError(f"Invalid {name}")
    if s["width"] <= 0 or s["height"] <= 0:
        raise ValueError("Shapes need positive width and height")
    if s["x"] + s["width"] > 612 or s["y"] + s["height"] > 792:
        raise ValueError("Shape outside default page")
    for c in ("fill", "stroke"):
        v = s.get(c)
        if v is not None and (not isinstance(v, str) or (v != "none" and not re.fullmatch(r"#[0-9a-fA-F]{6}", v))):
            raise ValueError("Paint must be a six-digit hex color or none")
    v = s.get("strokeWidth", 0)
    if not isinstance(v, (int, float)) or isinstance(v, bool) or not (0 <= v <= 30):
        raise ValueError("Invalid stroke width")
for shape in shapes:
    check_shape(shape)

stderr = (output / "mcp-server-stderr.log").open("w", encoding="utf-8")
proc = subprocess.Popen(
    ["vectorcraft-cli", "mcp", "--headless", "--automation-read-root", str(output),
     "--automation-write-root", str(output)],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr,
    text=True, bufsize=1,
)
counter = 0

def rpc(method, params=None, notification=False):
    global counter
    if proc.poll() is not None:
        raise RuntimeError(f"VectorCraft MCP exited with code {proc.returncode}")
    request_msg = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        request_msg["params"] = params
    if not notification:
        counter += 1
        request_msg["id"] = counter
    proc.stdin.write(json.dumps(request_msg) + "\n")
    proc.stdin.flush()
    if notification:
        return None
    while True:
        line = proc.stdout.readline()
        if not line:
            raise RuntimeError("MCP closed without a reply")
        response = json.loads(line)
        if response.get("id") != counter:
            continue
        if "error" in response:
            raise RuntimeError(f"MCP {method} protocol error: {response['error']}")
        result = response.get("result", {})
        if method == "tools/call" and result.get("isError"):
            raise RuntimeError(f"MCP {method} tool error: {result.get('content')}")
        return result

try:
    init = rpc("initialize", {
        "protocolVersion": "2025-06-18", "capabilities": {},
        "clientInfo": {"name": "vectorcraft-github-actions-bridge", "version": "1.0"},
    })
    rpc("notifications/initialized", notification=True)
    available = rpc("tools/list", {})
    names = [v["name"] for v in available.get("tools", [])]
    required = ["draw_shape", "save_file", "export"]
    if any(n not in names for n in required):
        raise RuntimeError(f"Missing MCP tools: {set(required) - set(names)}")

    # Headless sessions can open with a blank active document. Prefer an explicit new one.
    try:
        rpc("tools/call", {"name": "command_run",
                           "arguments": {"id": "file.new", "params": {"width": 612, "height": 792}}})
    except RuntimeError as exc:
        print("file.new not available; try active default document:", str(exc)[:200])

    for shape in shapes:
        reply = rpc("tools/call", {"name": "draw_shape", "arguments": shape})
        print("DRAW", shape["shape"], "OK", str(reply)[:160])

    for name, args in [
        ("save_file", {"path": str(output / "arte.vectorcraft")}),
        ("export", {"path": str(output / "arte.svg"), "format": "svg"}),
        ("export", {"path": str(output / "arte.png"), "format": "png"}),
    ]:
        rpc("tools/call", {"name": name, "arguments": args})
        print("PASS", name, args["path"])

    for filename in ("arte.vectorcraft", "arte.svg", "arte.png"):
        p = output / filename
        if not p.is_file() or p.stat().st_size < 100:
            raise RuntimeError(f"Missing or empty exported file: {filename}")
    report = {
        "status": "PASS",
        "serverInfo": init.get("serverInfo", {}),
        "mcp_tool_count": len(names),
        "mcp_tools": names,
        "shapes_drawn": len(shapes),
        "files": {p.name: p.stat().st_size for p in output.glob("arte.*")},
    }
    (output / "mcp-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("PASS VectorCraft REAL MCP", report["mcp_tool_count"], "tools", report["files"])
finally:
    proc.terminate()
    try:
        proc.wait(timeout=4)
    except subprocess.TimeoutExpired:
        proc.kill()
    stderr.close()
