"""Offline tests: model text alone must not qualify as evidence of an Edit."""
import json
import tempfile
import unittest
from pathlib import Path
from claude_edit_audit import verify_edit_stream


def item(kind, **details):
    return json.dumps({"type": kind, **details})


def tool_event(name, file_path, call_id, old=None, new=None):
    args = {"file_path": file_path}
    if name == "Edit":
        args.update({"old_string": old, "new_string": new})
    return item("assistant", message={"content": [{
        "type": "tool_use", "name": name, "id": call_id, "input": args,
    }]})


def tool_answer(call_id, error=False):
    return item("user", message={"content": [{
        "type": "tool_result", "tool_use_id": call_id, "is_error": error,
        "content": "success",
    }]})


class EditAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "task.txt"
        self.path.write_text("status: before\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def transcript(self, *, edit_tool="Edit", edit_path="task.txt", edited=True,
                   include_result=True, error=False):
        lines = [
            tool_event("Read", "task.txt", "r1"),
            tool_answer("r1"),
        ]
        if edited:
            lines.append(tool_event(edit_tool, edit_path, "e1", "status: before", "status: after"))
            if include_result:
                lines.append(tool_answer("e1", error=error))
        lines.append(item("result", result="DONE", is_error=False))
        return "\n".join(lines)

    def test_accepts_real_read_then_exact_edit(self):
        self.assertTrue(verify_edit_stream(self.transcript(), str(self.path))["ok"])

    def test_does_not_trust_final_answer(self):
        self.assertFalse(verify_edit_stream(item("result", result="DONE"), str(self.path))["ok"])

    def test_rejects_no_edit_or_fake_tool(self):
        self.assertFalse(verify_edit_stream(self.transcript(edited=False), str(self.path))["ok"])
        self.assertFalse(verify_edit_stream(self.transcript(edit_tool="Bash"), str(self.path))["ok"])

    def test_rejects_other_file_and_parent_traversal(self):
        self.assertFalse(verify_edit_stream(self.transcript(edit_path="other.txt"), str(self.path))["ok"])
        self.assertFalse(verify_edit_stream(self.transcript(edit_path="../other.txt"), str(self.path))["ok"])

    def test_rejects_missing_tool_result_and_errors(self):
        self.assertFalse(verify_edit_stream(self.transcript(include_result=False), str(self.path))["ok"])
        self.assertFalse(verify_edit_stream(self.transcript(error=True), str(self.path))["ok"])

    def test_rejects_malformed_stream(self):
        self.assertFalse(verify_edit_stream("not json\n" + self.transcript(), str(self.path))["ok"])

    def test_rejects_extra_tool_call(self):
        transcript = self.transcript()
        transcript += "\n" + tool_event("Write", "task.txt", "w1")
        self.assertFalse(verify_edit_stream(transcript, str(self.path))["ok"])


if __name__ == "__main__":
    unittest.main()
