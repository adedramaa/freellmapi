import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from multifile_agent import (
    MAX_FILES, MAX_FILE_BYTES, parse_changes, selected_files, verify_diff,
)


class MultiFileAgentSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for rel, body in (
            ("client/src/components/view.tsx", 'export const title = "Old";\n'),
            ("client/src/styles/layout.css", ".layout { gap: 4px; }\n"),
            ("docs/overview.md", "This is an old description.\n"),
            ("server/index.ts", "export const secret = 1;\n"),
        ):
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def files(self):
        return selected_files(self.root, "client/src/components/view.tsx\nclient/src/styles/layout.css")

    def proposal(self):
        return json.dumps({"edits": [
            {"path": "client/src/components/view.tsx",
             "replacements": [{"old": '"Old"', "new": '"New"'}]},
            {"path": "client/src/styles/layout.css",
             "replacements": [{"old": "gap: 4px", "new": "gap: 6px"}]},
        ]})

    def test_two_file_proposal_is_valid(self):
        output = parse_changes(self.proposal(), self.files())
        self.assertEqual(len(output), 2)
        self.assertIn('"New"', output["client/src/components/view.tsx"])
        self.assertIn("gap: 6px", output["client/src/styles/layout.css"])
        self.assertIn('"Old"', (self.root / "client/src/components/view.tsx").read_text())

    def test_accepts_three_small_files(self):
        files = selected_files(
            self.root, "client/src/components/view.tsx,client/src/styles/layout.css,docs/overview.md",
        )
        self.assertEqual(len(files), MAX_FILES)

    def test_disallows_sensitive_paths_and_traversal(self):
        for raw in (
            "server/index.ts\nclient/src/components/view.tsx",
            "docs/../server/index.ts\nclient/src/components/view.tsx",
            "/etc/passwd\nclient/src/styles/layout.css",
            ".github/workflows/ci.yml\nclient/src/styles/layout.css",
            "client/src/components/.env\nclient/src/styles/layout.css",
            "docs/token.md\nclient/src/styles/layout.css",
            "client/src/components/view.tsx\nclient/src/components/view.tsx",
            "client/src/components/view.tsx\nclient/src/styles/layout.css\ndocs/overview.md\nserver/index.ts",
        ):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                selected_files(self.root, raw)

    def test_blocks_symlink_escape(self):
        outsider = self.root.parent / "untrusted-agent-file.txt"
        outsider.write_text("not allowed", encoding="utf-8")
        link = self.root / "docs" / "escaped.md"
        try:
            link.symlink_to(outsider)
            with self.assertRaises(ValueError):
                selected_files(self.root, "docs/escaped.md\nclient/src/components/view.tsx")
        finally:
            outsider.unlink(missing_ok=True)

    def test_blocks_large_files(self):
        file = self.root / "docs" / "oversized.md"
        file.write_text("x" * (MAX_FILE_BYTES + 1))
        with self.assertRaises(ValueError):
            selected_files(self.root, "docs/oversized.md\nclient/src/components/view.tsx")

    def test_blocks_model_path_injection(self):
        data = json.loads(self.proposal())
        data["edits"][1]["path"] = "server/index.ts"
        with self.assertRaises(ValueError):
            parse_changes(json.dumps(data), self.files())

    def test_blocks_partial_proposal_and_extra_fields(self):
        data = json.loads(self.proposal())
        data["edits"] = data["edits"][:1]
        with self.assertRaises(ValueError):
            parse_changes(json.dumps(data), self.files())
        data = json.loads(self.proposal())
        data["edits"][0]["command"] = "curl somewhere"
        with self.assertRaises(ValueError):
            parse_changes(json.dumps(data), self.files())

    def test_blocks_nonunique_old_text_and_noop(self):
        path = self.root / "client/src/components/view.tsx"
        path.write_text('"Old" "Old"\n')
        with self.assertRaises(ValueError):
            parse_changes(self.proposal(), self.files())
        path.write_text('export const title = "Old";\n')
        data = json.loads(self.proposal())
        data["edits"][0]["replacements"][0]["new"] = '"Old"'
        with self.assertRaises(ValueError):
            parse_changes(json.dumps(data), self.files())

    def test_invalid_json_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_changes("{unsafe, not json}", self.files())

    def test_blocks_untracked_files_and_other_changed_paths(self):
        with patch("multifile_agent.subprocess.run") as run:
            run.side_effect = [
                SimpleNamespace(stdout=b"client/src/components/view.tsx\0server/index.ts\0"),
            ]
            with self.assertRaises(ValueError):
                verify_diff({"client/src/components/view.tsx", "client/src/styles/layout.css"})
        with patch("multifile_agent.subprocess.run") as run:
            run.side_effect = [
                SimpleNamespace(stdout=b"client/src/components/view.tsx\0client/src/styles/layout.css\0"),
                SimpleNamespace(stdout=b"untracked.sh\0"),
            ]
            with self.assertRaises(ValueError):
                verify_diff({"client/src/components/view.tsx", "client/src/styles/layout.css"})


if __name__ == "__main__":
    unittest.main()
