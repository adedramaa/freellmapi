"""Tests for owner-only ChatGPT -> push dispatch -> Claude Code bridge."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

from claude_issue_bridge import get_request, inspect_tool_stream, validate_diff, commit_changes


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
            "after": "a" * 40,
            "head_commit": {
                "id": "a" * 40,
                "message": "claude-task: " + json.dumps(self.spec),
            },
            "commits": [{"id": "a" * 40}],
        }
        self.patch_changes = patch(
            "claude_issue_bridge.commit_changes",
            return_value=[("A", ".claude-requests/task-20261021-pilot.json")],
        )
        self.fake_changes = self.patch_changes.start()

    def tearDown(self):
        self.patch_changes.stop()
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
        self.fake_changes.return_value = [("A", ".github/workflows/ci.yml")]
        with self.assertRaises(ValueError):
            get_request(self.root, self.event)

    def test_rejects_multifile_push_or_modified_files(self):
        self.fake_changes.return_value = [("A", ".claude-requests/task-20261021-pilot.json"), ("A", "docs/other.md")]
        with self.assertRaises(ValueError):
            get_request(self.root, self.event)
        self.fake_changes.return_value = [("M", ".claude-requests/task-20261021-pilot.json")]
        with self.assertRaises(ValueError):
            get_request(self.root, self.event)

    def test_real_git_diff_tree_checker(self):
        with patch("claude_issue_bridge.subprocess.run") as run:
            run.side_effect = [
                SimpleNamespace(stdout=b""),
                SimpleNamespace(stdout=b"A\t.claude-requests/task-20261021-pilot.json\n"),
            ]
            changes = commit_changes(self.root, "a" * 40)
            self.assertEqual(changes, [("A", ".claude-requests/task-20261021-pilot.json")])
            self.assertIn("fetch", run.call_args_list[0].args[0])
            self.assertIn("diff-tree", run.call_args_list[1].args[0])

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
