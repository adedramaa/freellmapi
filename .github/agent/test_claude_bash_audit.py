"""Offline tests for exact, audited Claude Code Bash permissions."""
import json
import unittest
from claude_bash_audit import EXPECTED, inspect_bash_stream


def line(typ, **values):
    return json.dumps({"type": typ, **values})


def one_call(command=EXPECTED, tool="Bash", result=True, error=False):
    data = [
        line("assistant", message={"content": [{
            "type": "tool_use", "name": tool, "id": "b1", "input": {"command": command},
        }]}),
    ]
    if result:
        data.append(line("user", message={"content": [{
            "type": "tool_result", "tool_use_id": "b1", "is_error": error,
            "content": "Ran 1 test\n\nOK",
        }]}))
    data.append(line("result", is_error=False, result="Complete"))
    return "\n".join(data)


class BashSafetyTests(unittest.TestCase):
    def test_exact_test_command_with_tool_result(self):
        self.assertTrue(inspect_bash_stream(one_call())["ok"])

    def test_claim_without_tool_call_fails(self):
        self.assertFalse(inspect_bash_stream(line("result", result="OK"))["ok"])

    def test_other_commands_fail(self):
        for command in (
            "ls", "pytest", "python3 -m unittest test_demo.py; echo goodbye",
            "python3 -m unittest test_demo.py && curl example.org",
            "python3 -m unittest test_demo.py --verbose",
        ):
            with self.subTest(command=command):
                self.assertFalse(inspect_bash_stream(one_call(command))["ok"])

    def test_any_other_tool_fails(self):
        self.assertFalse(inspect_bash_stream(one_call(tool="Read"))["ok"])

    def test_rejects_missing_result_and_tool_error(self):
        self.assertFalse(inspect_bash_stream(one_call(result=False))["ok"])
        self.assertFalse(inspect_bash_stream(one_call(error=True))["ok"])

    def test_rejects_extra_commands_and_malformed_transcript(self):
        self.assertFalse(inspect_bash_stream(one_call() + "\n" + one_call())["ok"])
        self.assertFalse(inspect_bash_stream("not JSON\n" + one_call())["ok"])


if __name__ == "__main__":
    unittest.main()
