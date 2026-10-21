"""Audit Claude Code stream-json without exposing prompts or raw tool output."""
import json

def inspect_stream(raw: str, expected: str) -> dict:
    tool_calls = []
    results = 0
    answer = ""
    errors = False
    for line in raw.splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(item, dict):
            continue
        if item.get("type") in ("assistant", "user"):
            message = item.get("message", {})
            blocks = message.get("content", []) if isinstance(message, dict) else []
            if isinstance(blocks, list):
                for block in blocks:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_use":
                        tool_calls.append(block.get("name"))
                    elif block.get("type") == "tool_result":
                        results += 1
        if item.get("type") == "result":
            errors = errors or bool(item.get("is_error"))
            answer = item.get("result", "") if isinstance(item.get("result"), str) else ""
    return {
        "ok": not errors and tool_calls == ["Read"] and results > 0 and answer.strip() == expected,
        "tool_calls": tool_calls,
        "tool_results": results,
        "answer_matches_fixture": answer.strip() == expected,
        "errored": errors,
    }
