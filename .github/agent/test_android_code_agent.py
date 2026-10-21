import tempfile
import unittest
from pathlib import Path
from android_code_agent import validate_path, validate_proposal, validate_task, unwrap_response


class AgentSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'client' / 'src' / 'components').mkdir(parents=True)
        (self.root / 'docs').mkdir()
        (self.root / 'server').mkdir()
        (self.root / 'client' / 'src' / 'components' / 'example.tsx').write_text('export const X = 1\n')
        (self.root / 'docs' / 'guide.md').write_text('# Guide\n')
        (self.root / 'server' / 'index.ts').write_text('const secret = 1\n')

    def tearDown(self):
        self.temp.cleanup()

    def test_allows_documentation_and_frontend(self):
        self.assertEqual(validate_path(self.root, 'docs/guide.md').name, 'guide.md')
        self.assertEqual(validate_path(self.root, 'client/src/components/example.tsx').suffix, '.tsx')

    def test_blocks_traversal_and_server_files(self):
        for path in ('../x.md', '/tmp/x.md', 'server/index.ts', '.github/workflows/ci.yml',
                     'docs/../server/index.ts', 'client/src/components/.env', 'docs/token.md'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                validate_path(self.root, path)

    def test_task_validation(self):
        self.assertEqual(validate_task('   Improve this description  '), 'Improve this description')
        with self.assertRaises(ValueError):
            validate_task('short')

    def test_proposal_rejects_unrelated_rewrites(self):
        original = 'const value = 1;\n' * 150
        with self.assertRaises(ValueError):
            validate_proposal(original, 'this is not related to the source\n')

    def test_fences(self):
        self.assertEqual(unwrap_response((chr(96) * 3) + 'ts\nexport const x = 1\n' + (chr(96) * 3)), 'export const x = 1')
        self.assertEqual(unwrap_response('hello'), 'hello')


if __name__ == '__main__':
    unittest.main()
