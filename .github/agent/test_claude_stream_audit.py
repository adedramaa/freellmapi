"""Offline assertions: never trust model text as evidence of tool execution."""
import json
import unittest
from claude_stream_audit import inspect_stream

TOKEN = "atlantic-cedar-4267"


def event(kind, content=None, **other):
    obj = {"type": kind, **other}
    if content is not None:
        obj["message"] = {"content": content}
    return json.dumps(obj)


def transcript(tool="Read", answer=TOKEN, tool_result=True, error=False):
    lines = [
        event("assistant", [{"type": "tool_use", "name": tool, "id": "tool-1",
                             "input": {"file_path": "docs/CLAUDE_TOOL_READ_FIXTURE.md"}}]),
    ]
    if tool_result:
        lines.append(event("user", [{"type": "tool_result", "tool_use_id": "tool-1",
                                      "content": "tool-read-proof: " + TOKEN}]))
    lines.append(event("result", result=answer, is_error=error))
    return "\n".join(lines)


class ReadToolEvidenceTests(unittest.TestCase):
    def test_valid_read_with_real_tool_result_and_exact_answer(self):
        self.assertTrue(inspect_stream(transcript(), TOKEN)["ok"])

    def test_answer_without_tool_call_does_not_count(self):
        self.assertFalse(inspect_stream(event("result", result=TOKEN), TOKEN)["ok"])

    def test_denies_shell_and_write_tool_use(self):
        for name in ("Bash", "Edit", "Write", "WebFetch"):
            with self.subTest(tool=name):
                self.assertFalse(inspect_stream(transcript(tool=name), TOKEN)["ok"])

    def test_requires_tool_result_and_correct_answer(self):
        self.assertFalse(inspect_stream(transcript(tool_result=False), TOKEN)["ok"])
        self.assertFalse(inspect_stream(transcript(answer="made up"), TOKEN)["ok"])

    def test_rejects_error_result(self):
        self.assertFalse(inspect_stream(transcript(error=True), TOKEN)["ok"])

    def test_ignores_malformed_stream_lines_without_assuming_success(self):
        self.assertFalse(inspect_stream("not-json\n{}\n", TOKEN)["ok"])


if __name__ == "__main__":
    unittest.main()
