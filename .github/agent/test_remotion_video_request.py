import json
from pathlib import Path
import tempfile
import unittest

from remotion_video_request import apply_claude, validate_spec, write_files


class VideoRequestTest(unittest.TestCase):
    def setUp(self):
        self.spec = {
            "title": "Video de prueba",
            "subtitle": "Desde el chat",
            "seconds": 3,
            "prompt": "Animación moderna sobre creatividad",
            "scenes": [
                {"heading": "CREAR", "caption": "Una idea se vuelve video"},
                {"heading": "EXPORTAR", "caption": "Directo en MP4"},
            ],
        }

    def test_validate(self):
        result = validate_spec(self.spec)
        self.assertEqual(result["seconds"], 3)
        self.assertEqual(len(result["scenes"]), 2)

    def test_reject_external_fields(self):
        with self.assertRaises(ValueError):
            validate_spec({**self.spec, "script": "rm -rf ."})

    def test_reject_long_videos(self):
        with self.assertRaises(ValueError):
            validate_spec({**self.spec, "seconds": 100})

    def test_reject_invalid_scene_data(self):
        with self.assertRaises(ValueError):
            validate_spec({**self.spec, "scenes": [{"heading": "<x>"}]})

    def test_reject_control_character(self):
        with self.assertRaises(ValueError):
            validate_spec({**self.spec, "title": "abc\nxyz"})

    def test_zombie_template_is_only_fixed_40_seconds(self):
        zombie = {**self.spec, "kind": "zombie-episode-1", "seconds": 40}
        validated = validate_spec(zombie)
        self.assertEqual(validated["kind"], "zombie-episode-1")
        self.assertEqual(validated["seconds"], 40)
        with self.assertRaises(ValueError):
            validate_spec({**zombie, "seconds": 120})
        with self.assertRaises(ValueError):
            validate_spec({**zombie, "seconds": 15})
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory)
            write_files(validated, dest)
            self.assertEqual((dest / "duration.txt").read_text(), "1200")
            self.assertFalse(json.loads((dest / "props.json").read_text())["hasVoice"])

    def test_zombie_rejects_bad_storyboard(self):
        zombie = {**self.spec, "kind": "zombie-episode-1", "seconds": 40}
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory)
            write_files(validate_spec(zombie), dest)
            with self.assertRaises(ValueError):
                apply_claude('[{"heading":"ONE","caption":"Not enough scenes"}]', dest)

    def test_write_and_reject_bad_claude(self):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory)
            write_files(validate_spec(self.spec), dest)
            self.assertEqual(json.loads((dest / "props.json").read_text())["title"], self.spec["title"])
            self.assertEqual((dest / "duration.txt").read_text(), "90")
            with self.assertRaises(ValueError):
                apply_claude('[{"heading": "X", "caption": "Y", "danger": "foo"}]', dest)
            apply_claude('[{"heading":"LISTO","caption":"Animado"}]', dest)
            self.assertEqual(json.loads((dest / "props.json").read_text())["scenes"][0]["heading"], "LISTO")


if __name__ == "__main__":
    unittest.main()
