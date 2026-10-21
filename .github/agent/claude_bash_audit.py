"""Check actual Claude Code Bash tool calls against one exact approved test command."""
import json
import sys
from pathlib import Path

EXPECTED = "python3 -m unittest test_demo.py"


def inspect_bash_stream(raw: str) -> dict:
    commands = []
    tool_ids = []
    results = set()
    errors = False
    completed = False
    for line in raw.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            errors = True
            continue
        if not isinstance(event, dict):
            errors = True
            continue
        if event.get("type") in ("assistant", "user"):
            msg = event.get("message")
            blocks = msg.get("content") if isinstance(msg, dict) else []
            if not isinstance(blocks, list):
                continue
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    if block.get("name") != "Bash":
                        errors = True
                    args = block.get("input")
                    cmd = args.get("command") if isinstance(args, dict) else None
                    commands.append(cmd)
                    tool_ids.append(block.get("id"))
                if block.get("type") == "tool_result":
                    if block.get("is_error"):
                        errors = True
                    if isinstance(block.get("tool_use_id"), str):
                        results.add(block["tool_use_id"])
        if event.get("type") == "result":
            completed = True
            if event.get("is_error"):
                errors = True
    ok = (
        not errors and completed
        and commands == [EXPECTED]
        and len(tool_ids) == 1 and isinstance(tool_ids[0], str)
        and results == set(tool_ids)
    )
    return {
        "ok": ok, "command_exact": commands == [EXPECTED],
        "bash_calls": len(commands), "tool_results": len(results),
        "finished": completed, "no_unapproved_tool": not errors,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: claude_bash_audit.py STREAM_JSONL")
    report = inspect_bash_stream(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print("Claude Bash test-tool audit:", json.dumps(report, sort_keys=True))
    if not report["ok"]:
        raise SystemExit("FAIL: permitted Bash test tool use not proven.")
    print("PASS: Claude Code executed only the exact approved unit-test command.")
