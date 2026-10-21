"""Tests for owner-only ChatGPT -> Issue -> genuine Claude Code bridge."""
import json
import tempfile
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
        self.event = {
            "action": "opened",
            "repository": {"full_name": "adedramaa/freellmapi"},
            "issue": {
                "title": "[claude-task] ChatGPT code proposal",
                "state": "open",
                "user": {"login": "adedramaa"},
                "body": json.dumps({
                    "file": "docs/demo.md",
                    "task": "Improve the short explanatory line without changing the heading.",
                }),
            },
        }

    def tearDown(self):
        self.tmp.cleanup()

    def test_accepts_owner_public_docs_request(self):
        rel, task, path = get_request(self.root, self.event)
        self.assertEqual(rel, "docs/demo.md")
        self.assertEqual(path, self.target)
        self.assertIn("Improve", task)

    def test_rejects_non_owner_or_other_repo(self):
        self.event["issue"]["user"]["login"] = "someone-else"
        with self.assertRaises(ValueError):
            get_request(self.root, self.event)
        self.event["issue"]["user"]["login"] = "adedramaa"
        self.event["repository"]["full_name"] = "other/repo"
        with self.assertRaises(ValueError):
            get_request(self.root, self.event)

    def test_rejects_wrong_title_and_event_and_modified_issue(self):
        for field, value in (("title", "Please run Claude"), ("state", "closed")):
            old = self.event["issue"][field]
            self.event["issue"][field] = value
            with self.assertRaises(ValueError):
                get_request(self.root, self.event)
            self.event["issue"][field] = old
        self.event["action"] = "edited"
        with self.assertRaises(ValueError):
            get_request(self.root, self.event)

    def test_rejects_unrequested_or_sensitive_files(self):
        for bad in ("../docs/demo.md", ".github/workflows/ci.yml",
                    "server/index.ts", "docs/secret.md"):
            self.event["issue"]["body"] = json.dumps({"file": bad, "task": "Improve public note."})
            with self.subTest(bad=bad), self.assertRaises((ValueError, OSError)):
                get_request(self.root, self.event)

    def test_rejects_bad_json_and_extra_fields(self):
        for body in ("{bad", json.dumps({"file": "docs/demo.md", "task": "Improve public note.", "extra": 1})):
            self.event["issue"]["body"] = body
            with self.subTest(body=body), self.assertRaises(ValueError):
                get_request(self.root, self.event)

    def test_rejects_malicious_control_and_unbounded_task(self):
        for task in ("tiny", "change it\nmore", "x" * 351):
            self.event["issue"]["body"] = json.dumps({"file": "docs/demo.md", "task": task})
            with self.subTest(task=task[:10]), self.assertRaises(ValueError):
                get_request(self.root, self.event)

    def test_validates_small_diff_only(self):
        original = self.target.read_text()
        validate_diff(original, original.replace("Original", "Updated"))
        for bad in (original, "", "X" * 6001, "# replacement\n" * 50):
            with self.subTest(size=len(bad)), self.assertRaises(ValueError):
                validate_diff(original, bad)

    def test_tool_evidence_requires_actual_read_and_edit(self):
        path = "docs/demo.md"
        def tool(name, tool_id):
            args = {"file_path": path}
            if name == "Edit":
                args.update(old_string="Original", new_string="Updated")
            return json.dumps({"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": name, "id": tool_id, "input": args}]}})
        def answer(tool_id):
            return json.dumps({"type": "user", "message": {"content": [
                {"type": "tool_result", "tool_use_id": tool_id, "content": "success"}]}})
        finish = json.dumps({"type": "result", "is_error": False, "result": "Done"})
        events = [tool("Read", "r"), answer("r"), tool("Edit", "e"), answer("e"), finish]
        self.assertTrue(inspect_tool_stream("\n".join(events), self.target, self.root)["ok"])
        self.assertFalse(inspect_tool_stream(finish, self.target, self.root)["ok"])
        self.assertFalse(inspect_tool_stream("\n".join(events[:-2] + [finish]), self.target, self.root)["ok"])
        self.assertFalse(inspect_tool_stream("\n".join(events[:2] + [tool("Bash", "b"), answer("b"), finish]),
                                             self.target, self.root)["ok"])
        self.assertFalse(inspect_tool_stream("\n".join(events[:2] + [
            tool("Edit", "e").replace(path, "../unauthorised.md"), answer("e"), finish]),
            self.target, self.root)["ok"])


if __name__ == "__main__":
    unittest.main()
