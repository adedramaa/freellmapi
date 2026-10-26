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
        print("CLAUDE_DIAGNOSTIC:", summarize_status(data))
        sys.exit(0)
    if mode != "assert":
        raise ValueError("Unknown command")
    result = proof(data)
    print("CLAUDE_SKILL_PROOF:", result)
    if not result["skill_invoked"] or result["tool_error"] or not result["nonempty_reply"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
