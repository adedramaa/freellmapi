"""Validate a real Claude Code Read/Edit demo before retaining its synthetic artifact.

No clients, credentials, production deployment, commits or API access.
This check is intentionally limited to one harmless public fixture.
"""
from __future__ import annotations
import json
from pathlib import Path
import re
import subprocess
import sys

TARGET = "agencia-autonoma/sandbox/claude-price-fixture.mjs"

def validate(root: Path, transcript: Path) -> dict:
    root = root.resolve(strict=True)
    path = (root / TARGET).resolve(strict=True)
    if not path.is_relative_to(root) or path.is_symlink():
        raise ValueError("Invalid fixture path")
    original = subprocess.run(["git", "show", "HEAD:" + TARGET], cwd=root,
                              capture_output=True, text=True, check=True).stdout
    current = path.read_text(encoding="utf-8")
    if original == current or not current.endswith("\n"):
        raise ValueError("Claude Code did not produce a valid source change")
    changes = subprocess.run(["git", "diff", "--name-only"], cwd=root,
                             capture_output=True, text=True, check=True).stdout.splitlines()
    if changes != [TARGET]:
        raise ValueError("Claude changed an unexpected repository file")
    subprocess.run(["git", "diff", "--check"], cwd=root, check=True,
                   stdout=subprocess.DEVNULL)
    stats = subprocess.run(["git", "diff", "--numstat", "--", TARGET], cwd=root,
                           capture_output=True, text=True, check=True).stdout.strip().split("\t")
    if len(stats) != 3 or not stats[0].isdigit() or not stats[1].isdigit() or             int(stats[0]) > 3 or int(stats[1]) > 3:
        raise ValueError("Change exceeds a small edit")
    if any(re.search(regex, current, re.I) for regex in
           [r"\bfetch\s*\(", r"\brequire\s*\(", r"\bimport\s*\(",
            r"\beval\s*\(", r"child_process", r"process\.env", r"https?://"]):
        raise ValueError("Unsafe new feature in synthetic fixture")
    if len(current.encode("utf-8")) > 1000 or "amountMinor" not in current:
        raise ValueError("Fixture replaced by unrelated code")
    tool_calls = []
    expected_results = set()
    returned_results = set()
    completed = False
    for raw_line in transcript.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError as ex:
            raise ValueError("Malformed Claude Code tool transcript") from ex
        if not isinstance(event, dict):
            raise ValueError("Invalid transcript event")
        if event.get("type") == "result":
            if event.get("is_error"):
                raise ValueError("Claude Code returned an error")
            completed = True
        if event.get("type") not in ("assistant", "user"):
            continue
        msg = event.get("message")
        blocks = msg.get("content") if isinstance(msg, dict) else []
        for item in blocks if isinstance(blocks, list) else []:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "tool_result":
                if item.get("is_error"):
                    raise ValueError("Claude Code tool failed")
                returned_results.add(item.get("tool_use_id"))
            if item.get("type") != "tool_use":
                continue
            name, uid, params = item.get("name"), item.get("id"), item.get("input")
            if name not in ("Read", "Edit") or not isinstance(uid, str) or not isinstance(params, dict):
                raise ValueError("Claude used an unapproved tool")
            requested = params.get("file_path")
            if not isinstance(requested, str):
                raise ValueError("Claude tool omitted exact fixture file path")
            selected = Path(requested)
            resolved = (selected if selected.is_absolute() else root / selected).resolve()
            if resolved != path:
                raise ValueError("Claude tool attempted another file")
            if name == "Edit" and not all(isinstance(params.get(k), str) for k in ("old_string", "new_string")):
                raise ValueError("Unsafe Edit call")
            tool_calls.append(name)
            expected_results.add(uid)
    if not completed or tool_calls not in (["Read", "Edit"], ["Read", "Edit", "Edit"]) or             len(expected_results) != len(tool_calls) or expected_results != returned_results:
        raise ValueError("No verified Claude Code Read/Edit execution")
    return {"ok": True, "kind": "synthetic_claude_code_smoke_v1", "file": TARGET,
            "tools": tool_calls, "added_lines": int(stats[0]),
            "deleted_lines": int(stats[1]), "model_provider": "FreeLLMAPI",
            "client_data_used": False, "deployment_performed": False,
            "auto_merge": False}

if __name__ == "__main__":
    try:
        result = validate(Path.cwd(), Path(sys.argv[1]))
        print(json.dumps(result, ensure_ascii=False))
    except (ValueError, OSError, IndexError, subprocess.CalledProcessError) as e:
        print("CLAUDE_SMOKE_REJECTED: " + str(e)[:220], file=sys.stderr)
        sys.exit(1)
