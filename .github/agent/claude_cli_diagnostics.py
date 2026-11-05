"""Summarize Claude CLI failures without leaking model output or credentials."""
import collections
import json
from pathlib import Path
import sys


def main(jsonl: Path, stderr_file: Path) -> None:
    events = []
    for line in jsonl.read_text(errors="replace").splitlines():
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                events.append(obj)
        except (ValueError, TypeError):
            pass
    counts = collections.Counter(
        str(obj.get("type", ""))[:35] for obj in events
    )
    results = [
        {
            "subtype": str(obj.get("subtype", ""))[:40],
            "is_error": bool(obj.get("is_error")),
            "num_turns": obj.get("num_turns")
            if isinstance(obj.get("num_turns"), int) else None,
        }
        for obj in events if obj.get("type") == "result"
    ]
    stderr = stderr_file.read_text(errors="replace").lower()
    signatures = [
        "429", "401", "402", "403", "500", "502", "503", "rate limit",
        "timeout", "context", "overloaded", "connection",
        "invalid request", "model not found", "authentication",
    ]
    print("Claude Code SAFE event counts:", dict(counts))
    print("Claude Code SAFE result metadata:", results[:3])
    print("Claude Code SAFE error categories:",
          [item for item in signatures if item in stderr])
    print("Claude Code SAFE stderr length:", len(stderr))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
