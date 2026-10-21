"""Verify that the official Claude Code CLI performed a genuine, constrained Edit."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def verify_edit_stream(raw: str, target_path: str) -> dict:
    target = Path(target_path).resolve(strict=True)
    calls: list[tuple[str, str]] = []
    results: set[str] = set()
    errors = False
    saw_final = False
    malformed = 0
    for line in raw.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            malformed += 1
            continue
        if not isinstance(event, dict):
            continue
        category = event.get("type")
        if category in ("assistant", "user"):
            message = event.get("message")
            blocks = message.get("content") if isinstance(message, dict) else None
            if not isinstance(blocks, list):
                continue
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    name, call_id = block.get("name"), block.get("id")
                    args = block.get("input")
                    path = args.get("file_path") if isinstance(args, dict) else None
                    if not isinstance(name, str) or not isinstance(call_id, str) or not isinstance(path, str):
                        errors = True
                        continue
                    # Neither relative path traversal nor another file is acceptable.
                    requested = Path(path)
                    actual_path = requested.resolve() if requested.is_absolute() else (target.parent / requested).resolve()
                    if actual_path != target:
                        errors = True
                    if name == "Edit":
                        if not isinstance(args.get("old_string"), str) or not isinstance(args.get("new_string"), str):
                            errors = True
                    calls.append((name, call_id))
                elif block.get("type") == "tool_result":
                    if block.get("is_error"):
                        errors = True
                    call_id = block.get("tool_use_id")
                    if isinstance(call_id, str):
                        results.add(call_id)
        elif category == "result":
            saw_final = True
            errors = errors or bool(event.get("is_error"))
    names = [name for name, _ in calls]
    unique_ids = len(set(call_id for _, call_id in calls)) == len(calls)
    # The tool must read before editing, and all tool outputs must arrive.
    valid_sequence = names in (["Read", "Edit"], ["Read", "Read", "Edit"])
    all_resolved = len(results) == len(calls) and results == {call_id for _, call_id in calls}
    ok = not errors and malformed == 0 and saw_final and unique_ids and valid_sequence and all_resolved
    return {
        "ok": ok, "tools": names, "tool_results": len(results),
        "finished": saw_final, "path_valid": not errors,
        "malformed_events": malformed,
    }


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: claude_edit_audit.py STREAM_FILE ABSOLUTE_FIXTURE_PATH")
    raw = Path(sys.argv[1]).read_text(encoding="utf-8")
    evidence = verify_edit_stream(raw, sys.argv[2])
    print("Edit-tool evidence:", json.dumps(evidence, sort_keys=True))
    if not evidence["ok"]:
        raise SystemExit("FAIL: genuine Read+Edit tool sequence not proven.")
    print("PASS: official Claude Code called Read and Edit on the expected local fixture.")


if __name__ == "__main__":
    main()
