"""Strict bridge from owner-authored GitHub dispatch commits to Claude Code draft PRs.

Dispatch content is PUBLIC; never send private user data or credentials.
The model job has read-only GitHub permissions; publication is a separate job.
"""
from __future__ import annotations

import difflib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from android_code_agent import validate_path

OWNER = "adedramaa"
REPOSITORY = OWNER + "/freellmapi"
MAX_FILE_BYTES = 4_500
MAX_TASK_LENGTH = 350
MAX_CHANGED_LINES = 35
MAX_RESULT_BYTES = 6_000


def commit_changes(root: Path, sha: str) -> list[tuple[str, str]]:
    """Inspect the ACTUAL Git commit, not optional push-webhook file summaries."""
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Invalid dispatch commit SHA.")
    subprocess.run(
        ["git", "fetch", "--no-tags", "--depth=2", "origin", sha],
        cwd=root, capture_output=True, check=True, timeout=40,
    )
    result = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-status", "-r", sha],
        cwd=root, capture_output=True, check=True, timeout=15,
    )
    items = []
    for line in result.stdout.decode("utf-8").splitlines():
        parts = line.split("\t", 1)
        if len(parts) != 2:
            raise ValueError("Unexpected Git diff-tree output.")
        items.append((parts[0], parts[1]))
    return items


def get_request(root: Path, event: dict) -> tuple[str, str, Path]:
    """Only an owner's single new dispatch-file push can invoke Claude Code."""
    if (
        event.get("ref") != "refs/heads/claude-requests"
        or (event.get("sender") or {}).get("login") != OWNER
        or (event.get("repository") or {}).get("full_name") != REPOSITORY
    ):
        raise ValueError("Not an authorized owner request.")
    commit = event.get("head_commit")
    commits = event.get("commits")
    if not isinstance(commit, dict) or not isinstance(commits, list) or len(commits) != 1:
        raise ValueError("Expected exactly one new dispatch commit.")
    sha = event.get("after")
    if sha != commit.get("id"):
        raise ValueError("Push head commit identity mismatch.")
    files = commit_changes(root, sha)
    if len(files) != 1 or files[0][0] != "A":
        raise ValueError("The real commit must add exactly one new request file.")
    request_path = files[0][1]
    if not re.fullmatch(
        r"\.claude-requests/task-[0-9]{8}-[a-z0-9-]{1,50}\.json", request_path
    ):
        raise ValueError("Invalid dispatch filename.")
    message = commit.get("message")
    if not isinstance(message, str) or not message.startswith("claude-task: "):
        raise ValueError("Request must use the exact claude-task commit prefix.")
    body = message[len("claude-task: "):]
    if len(body.encode("utf-8")) > 1_500:
        raise ValueError("Request metadata is too long.")
    try:
        spec = json.loads(body)
    except json.JSONDecodeError as exc:
        raise ValueError("Request commit must contain valid JSON.") from exc
    if type(spec) is not dict or set(spec) != {"file", "task"}:
        raise ValueError("JSON must contain exactly file and task.")
    rel, task = spec["file"], spec["task"]
    if type(rel) is not str or not re.fullmatch(r"[A-Za-z0-9_./-]{1,160}", rel):
        raise ValueError("Unsafe filename.")
    if type(task) is not str or not (12 <= len(task) <= MAX_TASK_LENGTH):
        raise ValueError("Task must be 12-350 characters.")
    if any(ord(c) < 32 or ord(c) == 127 for c in task):
        raise ValueError("Task must contain one line of ordinary text.")
    path = validate_path(root, rel)
    if root.joinpath(rel).is_symlink() or path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("File must be a small, regular source file.")
    return rel, task, path


def validate_diff(original: str, proposed: str) -> None:
    if not proposed or original == proposed or len(proposed.encode("utf-8")) > MAX_RESULT_BYTES:
        raise ValueError("Empty, unchanged or oversized generated file.")
    if "\0" in proposed:
        raise ValueError("Binary output rejected.")
    if not proposed.endswith("\n"):
        raise ValueError("Generated source must end with newline.")
    if len(proposed) > len(original) + 1_500:
        raise ValueError("Change expands the file excessively.")
    before, after = original.splitlines(keepends=True), proposed.splitlines(keepends=True)
    operations = difflib.SequenceMatcher(None, before, after, autojunk=False).get_opcodes()
    changed = sum(max(i2 - i1, j2 - j1)
                  for op, i1, i2, j1, j2 in operations if op != "equal")
    if not (1 <= changed <= MAX_CHANGED_LINES):
        raise ValueError("Too many changed lines (limit 35).")
    if len(original) > 1_000:
        ratio = difflib.SequenceMatcher(None, original, proposed, autojunk=False).ratio()
        if ratio < 0.65:
            raise ValueError("Unrelated rewrite rejected.")


def inspect_tool_stream(raw: str, allowed: Path, root: Path) -> dict:
    names: list[str] = []
    ids: list[str] = []
    responses: set[str] = set()
    valid = True
    result_seen = False
    for line in raw.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            valid = False
            continue
        if not isinstance(event, dict):
            valid = False
            continue
        if event.get("type") in ("assistant", "user"):
            message = event.get("message")
            blocks = message.get("content") if isinstance(message, dict) else []
            if not isinstance(blocks, list):
                continue
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    name, uid, arguments = block.get("name"), block.get("id"), block.get("input")
                    rel = arguments.get("file_path") if isinstance(arguments, dict) else None
                    if not isinstance(name, str) or not isinstance(uid, str) or not isinstance(rel, str):
                        valid = False
                        continue
                    target = Path(rel)
                    resolved = (target if target.is_absolute() else root / target).resolve()
                    if resolved != allowed:
                        valid = False
                    if name == "Edit":
                        if not isinstance(arguments.get("old_string"), str) or not isinstance(arguments.get("new_string"), str):
                            valid = False
                    names.append(name)
                    ids.append(uid)
                elif block.get("type") == "tool_result":
                    if block.get("is_error"):
                        valid = False
                    if isinstance(block.get("tool_use_id"), str):
                        responses.add(block["tool_use_id"])
        if event.get("type") == "result":
            result_seen = True
            valid = valid and not bool(event.get("is_error"))
    accepted = (
        valid and result_seen and len(ids) == len(set(ids))
        and names in (["Read", "Edit"], ["Read", "Read", "Edit"], ["Read", "Edit", "Edit"])
        and responses == set(ids)
    )
    return {"ok": accepted, "tools": names, "tool_results": len(responses), "completed": result_seen}


def verify_checkout(root: Path, expected: str) -> None:
    diff = subprocess.run(
        ["git", "diff", "--name-only", "-z"], cwd=root, capture_output=True, check=True,
    ).stdout
    changed = [part.decode("utf-8") for part in diff.split(b"\0") if part]
    if changed != [expected]:
        raise ValueError("Only the explicitly selected path can change.")
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=root, capture_output=True, check=True,
    ).stdout
    if untracked:
        raise ValueError("Untracked output in source checkout.")
    subprocess.run(["git", "diff", "--check"], cwd=root, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def run() -> None:
    if os.environ.get("GITHUB_REPOSITORY") != REPOSITORY:
        raise ValueError("Wrong GitHub repository.")
    if os.environ.get("GITHUB_EVENT_NAME") != "push" or os.environ.get("GITHUB_REF") != "refs/heads/claude-requests":
        raise ValueError("Only new owner task commits on the dispatch branch are supported.")
    root = Path.cwd().resolve(strict=True)
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
    rel, task, file = get_request(root, event)
    mode = sys.argv[1] if len(sys.argv) == 2 else ""
    if mode == "prepare":
        output = Path(os.environ["GITHUB_OUTPUT"])
        with output.open("a", encoding="utf-8") as stream:
            stream.write("file=" + rel + "\n")
        prompt = (
            "Use Read once on " + rel + ". Then use Edit to make ONE MINIMAL change "
            "only to that file, following this request: " + task +
            ". Do not read or edit any other files. No other tools or commands. "
            "Finish with a short confirmation."
        )
        Path(os.environ["RUNNER_TEMP"], "claude-chat-prompt.txt").write_text(prompt, encoding="utf-8")
        print("Owner, task and single file validated; no model called.")
        return
    if mode == "audit":
        raw = Path(os.environ["RUNNER_TEMP"], "claude-chat-stream.jsonl").read_text(encoding="utf-8")
        evidence = inspect_tool_stream(raw, file, root)
        print("Claude Code evidence:", json.dumps(evidence, sort_keys=True))
        if not evidence["ok"]:
            raise ValueError("No permitted Read/Edit tool sequence confirmed.")
        original = subprocess.run(
            ["git", "show", "HEAD:" + rel], cwd=root, capture_output=True, check=True,
        ).stdout.decode("utf-8")
        new = file.read_text(encoding="utf-8")
        validate_diff(original, new)
        verify_checkout(root, rel)
        target = Path(os.environ["RUNNER_TEMP"], "claude-chat-output", rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(file, target)
        print("PASS: authentic Claude Code edited one approved file; artifact ready for review.")
        return
    if mode == "stage":
        source_dir = Path(os.environ["PROPOSAL_DIR"]).resolve(strict=True)
        found = [p for p in source_dir.rglob("*") if p.is_file() or p.is_symlink()]
        if len(found) != 1 or found[0].is_symlink() or found[0].relative_to(source_dir).as_posix() != rel:
            raise ValueError("Proposal artifact does not contain the exact approved file.")
        original = file.read_text(encoding="utf-8")
        proposed = found[0].read_text(encoding="utf-8")
        validate_diff(original, proposed)
        file.write_text(proposed, encoding="utf-8")
        verify_checkout(root, rel)
        print("PASS: artifact staged with one validated change. Await human draft-PR review.")
        return
    raise ValueError("Unknown bridge operation.")


if __name__ == "__main__":
    try:
        run()
    except (ValueError, OSError, KeyError, UnicodeDecodeError, json.JSONDecodeError,
            subprocess.CalledProcessError) as error:
        print("Claude issue bridge blocked: " + str(error)[:190], file=sys.stderr)
        sys.exit(1)
