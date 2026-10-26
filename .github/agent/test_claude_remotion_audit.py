import json
import unittest
from claude_remotion_audit import proof, summarize_status

class ClaudeProofTest(unittest.TestCase):
    def test_tool_use_and_answer(self):
        content = "\n".join([
            json.dumps({"type":"assistant","message":{"content":[{"type":"tool_use","name":"Skill","id":"abc","input":{"skill":"remotion:remotion-best-practices"}}]}}),
            json.dumps({"type":"user","message":{"content":[{"type":"tool_result","tool_use_id":"abc","content":"Skill content..."}]}}),
            json.dumps({"type":"assistant","message":{"content":[{"type":"text","text":"Usa Sequence."}]}}),
        ])
        self.assertEqual(proof(content), {"skill_invoked": True, "nonempty_reply": True, "tool_error": False})
    def test_no_fake_proof(self):
        content=json.dumps({"type":"assistant","message":{"content":[{"type":"text","text":"I used Remotion."}]}})
        self.assertFalse(proof(content)["skill_invoked"])
    def test_error_result_fails(self):
        content="\n".join([
            json.dumps({"message":{"content":[{"type":"tool_use","name":"Skill","id":"k","input":{"skill":"remotion:remotion-render"}}]}}),
            json.dumps({"message":{"content":[{"type":"tool_result","tool_use_id":"k","is_error":True}]}}),
            json.dumps({"message":{"content":[{"type":"text","text":"oops"}]}})])
        self.assertTrue(proof(content)["tool_error"])
    def test_errors_are_categorized_without_secrets(self):
        self.assertEqual(summarize_status("Upstream returned 429 token=private"),"quota")
        self.assertEqual(summarize_status("Connection reset"),"transport")

if __name__=="__main__":
    unittest.main()
