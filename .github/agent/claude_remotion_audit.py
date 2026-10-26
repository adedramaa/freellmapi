"""Proof that Claude Code truly invoked Remotion plugin, not just installed it.

Never print raw streams, stderr, prompts, API responses, or credentials.
"""
from __future__ import annotations
import json
from pathlib import Path
import re
import sys


def summarize_status(text: str) -> str:
    text = text.lower()
    for category, regex in (
        ("authentication", r"401|403|invalid.api.key|unauthorized|authentication"),
        ("quota", r"429|rate.limit|quota|resource.exhausted"),
        ("upstream-unavailable", r"503|502|overloaded|unavailable|no providers"),
        ("timeout", r"timeout|timed out"),
        ("model-not-found", r"404|model.not.found"),
        ("transport", r"connection|fetch.failed|econn|socket"),
        ("unsupported-tool", r"unknown tool|unknown skill|not recognized|disable.*skill"),
        ("invalid-cli-option", r"unknown option|unrecognized option|invalid option|unsupported flag"),
        ("not-logged-in", r"not logged in|please log in|login required|no api key|missing.*key"),
        ("non-interactive", r"cannot run.*interactive|terminal.*required|prompt.*tty"),
        ("plugin-load", r"plugin.*(error|failed)|skill.*(error|failed)|cannot load.*skill"),
        ("invalid-cli-value", r"invalid.*(argument|value|choice)|expects.*argument"),
        ("failed-permission", r"permission denied|not permitted|restricted"),
        ("fatal-process", r"fatal error|uncaught|node.js v"),
    ):
        if re.search(regex, text):
            return category
    return "other"


def proof(lines: str) -> dict:
    invoked = False
    answered = False
    failed_result = False
    tool_id = None
    success_text = False
    for line in lines.splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            continue
        msg = item.get("message")
        if not isinstance(msg, dict):
            continue
        blocks = msg.get("content", [])
        if not isinstance(blocks, list):
            continue
        for b in blocks:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use" and b.get("name") == "Skill":
                inp = b.get("input", {})
                if isinstance(inp, dict) and "remotion" in str(inp.get("skill", "")).lower():
                    invoked = True
                    tool_id = b.get("id")
            if b.get("type") == "tool_result" and b.get("tool_use_id") == tool_id and b.get("is_error"):
                failed_result = True
            if b.get("type") == "text" and b.get("text", "").strip():
                answered = True
    return {"skill_invoked": invoked, "nonempty_reply": answered, "tool_error": failed_result}


def main():
    mode, name = sys.argv[1:3]
    data = Path(name).read_text(encoding="utf-8", errors="replace")
    if mode == "status":
        print("CLAUDE_DIAGNOSTIC:", summarize_status(data), "stderr_bytes:", len(data.encode()))
        sample = data.lower()
        terms = ("invalid", "unknown", "error", "fail", "login", "auth", "permission", "model", "token", "plugin", "skill", "url", "config", "setting", "prompt", "system", "tool")
        print("ERROR_KEYWORDS:", [w for w in terms if w in sample])
        sys.exit(0)
    if mode == "status-stream":
        records = []
        for line in data.splitlines():
            try:
                o = json.loads(line)
            except ValueError:
                continue
            rec = {"event": o.get("type"), "subtype": o.get("subtype")}
            if o.get("type") == "result":
                rec.update({"is_error": o.get("is_error"), "num_turns": o.get("num_turns"), "result_kind": summarize_status(str(o.get("result", "")))})
            if o.get("type") == "assistant":
                msg = o.get("message") or {}
                if isinstance(msg, dict):
                    rec["stop_reason"] = msg.get("stop_reason")
                    rec["blocks"] = [x.get("name", x.get("type")) for x in msg.get("content", []) if isinstance(x, dict)]
            if o.get("type") == "system":
                rec["tools_have_skill"] = "Skill" in o.get("tools", [])
            records.append(rec)
        print("STREAM_STATUS:", records[-7:])
        sys.exit(0)
    if mode != "assert":
        raise ValueError("Unknown command")
    result = proof(data)
    print("CLAUDE_SKILL_PROOF:", result)
    if not result["skill_invoked"] or result["tool_error"] or not result["nonempty_reply"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
