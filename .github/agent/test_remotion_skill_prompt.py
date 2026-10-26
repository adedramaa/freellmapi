import tempfile
from pathlib import Path
import unittest
from remotion_skill_prompt import build_prompt, locate_skill


class InstalledSkillTests(unittest.TestCase):
    def test_plugin_skill_is_used_as_prompt_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)
            for name in ("remotion-best-practices","remotion-render"):
                p=home / ".claude/plugins/cache/remotion/remotion/4.0.538/skills" / name / "SKILL.md"
                p.parent.mkdir(parents=True,exist_ok=True)
                p.write_text("---\nname: "+name+"\n---\nUse remotion timelines and animation.",encoding="utf-8")
            prompt, digests=build_prompt(home, "Return JSON for 5 scenes")
            self.assertIn("OFFICIAL REMOTION SKILL",prompt)
            self.assertIn("remotion-render=",digests)
            self.assertIn("Return JSON for 5 scenes",prompt)
            self.assertEqual(locate_skill(home,"remotion-render").name,"SKILL.md")

    def test_long_brief_rejected(self):
        with self.assertRaises(ValueError):
            build_prompt(Path("/tmp"),"x"*1601)


if __name__ == "__main__":
    unittest.main()
