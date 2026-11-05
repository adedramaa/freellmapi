"""Tests for owner-only ChatGPT -> push dispatch -> Claude Code bridge."""
import json
import tempfile
import os
import subprocess
from unittest.mock import patch
import unittest
from pathlib import Path

from claude_issue_bridge import get_request, inspect_tool_stream, validate_diff


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        target = self.root / "docs" / "demo.md"
        target.parent.mkdir(parents=True)
        target.write_text("# Example\n\nOriginal explanatory line.\n", encoding="utf-8")
        self.target = target
        self.spec = {"file": "docs/demo.md", "task": "Improve the short explanatory line without changing heading."}
        self.event = {
            "ref": "refs/heads/claude-requests",
            "sender": {"login": "adedramaa"},
            "repository": {"full_name": "adedramaa/freellmapi"},
            "head_commit": {
                "added": [".claude-requests/task-20261021-pilot.json"],
                "modified": [], "removed": [],
                "message": "claude-task: " + json.dumps(self.spec),
            },
            "commits": [{"id": "test-commit"}],
        }

    def tearDown(self):
        self.tmp.cleanup()

    def task(self, spec):
        self.event["head_commit"]["message"] = "claude-task: " + json.dumps(spec)

    def test_accepts_single_owner_task(self):
        rel, task, path = get_request(self.root, self.event)
        self.assertEqual(rel, "docs/demo.md")
        self.assertEqual(path, self.target)
        self.assertIn("Improve", task)

    def test_rejects_non_owner_or_other_repo(self):
        self.event["sender"]["login"] = "outsider"
        with self.assertRaises(ValueError):
            get_request(self.root, self.event)
        self.event["sender"]["login"] = "adedramaa"
        self.event["repository"]["full_name"] = "other/repo"
        with self.assertRaises(ValueError):
            get_request(self.root, self.event)

    def test_rejects_wrong_branch_and_unrelated_commit(self):
        self.event["ref"] = "refs/heads/main"
        with self.assertRaises(ValueError):
            get_request(self.root, self.event)
        self.event["ref"] = "refs/heads/claude-requests"
        self.event["head_commit"]["added"] = [".github/workflows/ci.yml"]
        with self.assertRaises(ValueError):
            get_request(self.root, self.event)

    def test_rejects_multifile_push_or_modified_files(self):
        self.event["head_commit"]["added"].append("docs/other.md")
        with self.assertRaises(ValueError):
            get_request(self.root, self.event)
        self.event["head_commit"]["added"] = [".claude-requests/task-20261021-pilot.json"]
        self.event["head_commit"]["modified"] = ["docs/other.md"]
        with self.assertRaises(ValueError):
            get_request(self.root, self.event)

    def test_rejects_sensitive_or_traversal_paths(self):
        for bad in ("../docs/demo.md", ".github/workflows/ci.yml", "server/index.ts", "docs/token.md"):
            self.task({"file": bad, "task": "Improve the public introduction."})
            with self.subTest(bad=bad), self.assertRaises((ValueError, OSError)):
                get_request(self.root, self.event)

    def test_rejects_malformed_json_and_extra_fields(self):
        for payload in ("{wrong", json.dumps({**self.spec, "extra": True})):
            self.event["head_commit"]["message"] = "claude-task: " + payload
            with self.assertRaises(ValueError):
                get_request(self.root, self.event)

    def test_rejects_control_chars_and_unbounded_task(self):
        for task in ("tiny", "change it\nmore", "x" * 351):
            self.task({"file": "docs/demo.md", "task": task})
            with self.subTest(task=task[:10]), self.assertRaises(ValueError):
                get_request(self.root, self.event)

    def test_missing_webhook_file_list_uses_verified_commit(self):
        self.event["head_commit"]["added"] = []
        with patch("claude_issue_bridge.confirm_added_request_from_git",
                   return_value=".claude-requests/task-20261021-pilot.json") as verified:
            rel, task, path = get_request(self.root, self.event)
            verified.assert_called_once_with(self.root, self.event)
            self.assertEqual(rel, "docs/demo.md")
            self.assertEqual(path, self.target)

    def test_commit_fallback_requires_matching_parent_and_single_added_path(self):
        sha = "a" * 40
        previous = "b" * 40
        self.event["head_commit"]["id"] = sha
        self.event["before"] = previous
        ok = lambda value: subprocess.CompletedProcess([], 0, stdout=value)
        with patch.dict(os.environ, {"GITHUB_SHA": sha}):
            with patch("claude_issue_bridge.subprocess.run", side_effect=[
                ok(""), ok(sha + " " + previous + "\n"),
                ok("A\t.claude-requests/task-20261021-pilot.json\n")
            ]):
                from claude_issue_bridge import confirm_added_request_from_git
                self.assertEqual(confirm_added_request_from_git(self.root, self.event),
                                 ".claude-requests/task-20261021-pilot.json")
            with patch("claude_issue_bridge.subprocess.run", side_effect=[
                ok(""), ok(sha + " " + previous + "\n"),
                ok("M\tdocs/demo.md\n")
            ]):
                with self.assertRaises(ValueError):
                    confirm_added_request_from_git(self.root, self.event)
            self.event["before"] = "c" * 40
            with patch("claude_issue_bridge.subprocess.run", side_effect=[
                ok(""), ok(sha + " " + previous + "\n")
            ]):
                with self.assertRaises(ValueError):
                    confirm_added_request_from_git(self.root, self.event)

    def test_diff_limited_to_small_change(self):
        original = self.target.read_text()
        validate_diff(original, original.replace("Original", "Updated"))
        for bad in (original, "", "X" * 6001, "# replacement\n" * 50):
            with self.subTest(chars=len(bad)), self.assertRaises(ValueError):
                validate_diff(original, bad)

    def test_audits_real_read_and_edit(self):
        path = "docs/demo.md"
        def tool(name, ident):
            args = {"file_path": path}
            if name == "Edit":
                args.update({"old_string": "Original", "new_string": "Updated"})
            return json.dumps({"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": name, "id": ident, "input": args}]}})
        def result(ident):
            return json.dumps({"type": "user", "message": {"content": [
                {"type": "tool_result", "tool_use_id": ident, "content": "success"}]}})
        end = json.dumps({"type": "result", "is_error": False, "result": "Done"})
        events = [tool("Read", "r"), result("r"), tool("Edit", "e"), result("e"), end]
        self.assertTrue(inspect_tool_stream("\n".join(events), self.target, self.root)["ok"])
        self.assertFalse(inspect_tool_stream(end, self.target, self.root)["ok"])
        self.assertFalse(inspect_tool_stream("\n".join(events[:-2] + [end]), self.target, self.root)["ok"])
        self.assertFalse(inspect_tool_stream("\n".join(events[:2] + [tool("Bash", "b"), result("b"), end]), self.target, self.root)["ok"])
        wrong = tool("Edit", "e").replace(path, "../unauthorised.md")
        self.assertFalse(inspect_tool_stream("\n".join(events[:2] + [wrong, result("e"), end]), self.target, self.root)["ok"])


if __name__ == "__main__":
    unittest.main()
