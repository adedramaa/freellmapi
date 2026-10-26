"""Validate narrowly scoped, owner-submitted Remotion jobs from chat.

All code runs from reviewed main. Untrusted request files are data, never executed.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys

REPOSITORY = "adedramaa/freellmapi"
OWNER = "adedramaa"
PATH_PATTERN = r"\.video-requests/video-[0-9]{8}-[a-z0-9-]{1,48}\.json"
HEX_COLOR = re.compile(r"#[0-9a-fA-F]{6}\Z")


def limited_text(value: object, max_length: int, required: bool = True) -> str:
    if not isinstance(value, str) or (required and not value.strip()) or len(value) > max_length:
        raise ValueError("Invalid text length/type")
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError("Control characters are not permitted")
    return value


def validate_spec(raw: object) -> dict:
    if not isinstance(raw, dict):
        raise ValueError("Request must be a JSON object")
    if set(raw) - {"title", "subtitle", "background", "accent", "scenes", "seconds", "prompt", "use_claude", "kind"}:
        raise ValueError("Unknown keys in request")
    title = limited_text(raw.get("title", ""), 36)
    subtitle = limited_text(raw.get("subtitle", ""), 90, required=False)
    prompt = limited_text(raw.get("prompt", ""), 320, required=False)
    kind = raw.get("kind", "motion")
    if kind not in ("motion", "zombie-episode-1"):
        raise ValueError("Unknown video composition")
    seconds = raw.get("seconds", 6)
    if type(seconds) is not int or not (seconds == 40 if kind == "zombie-episode-1" else 3 <= seconds <= 15):
        raise ValueError("Zombie video must be 40 seconds; other videos 3-15 seconds")
    background, accent = raw.get("background", "#0b1020"), raw.get("accent", "#76e8c7")
    if not isinstance(background, str) or not HEX_COLOR.fullmatch(background):
        raise ValueError("Background must be #RRGGBB")
    if not isinstance(accent, str) or not HEX_COLOR.fullmatch(accent):
        raise ValueError("Accent must be #RRGGBB")
    scenes = raw.get("scenes", [])
    if not isinstance(scenes, list) or len(scenes) > 5:
        raise ValueError("Maximum five scenes")
    validated = []
    for scene in scenes:
        if not isinstance(scene, dict) or set(scene) != {"heading", "caption"}:
            raise ValueError("Each scene must have heading and caption")
        validated.append({
            "heading": limited_text(scene["heading"], 36),
            "caption": limited_text(scene["caption"], 90, required=False),
        })
    if not validated and not prompt:
        raise ValueError("Provide scenes or prompt")
    use_claude = raw.get("use_claude", True)
    if type(use_claude) is not bool:
        raise ValueError("use_claude must be boolean")
    if not validated:
        validated = [{"heading": title, "caption": prompt[:90]}]
    return {
        "title": title,
        "subtitle": subtitle,
        "background": background,
        "accent": accent,
        "scenes": validated,
        "seconds": seconds,
        "prompt": prompt,
        "use_claude": use_claude,
        "kind": kind,
    }


def load_authorized_request(event: dict, root: Path) -> dict:
    if (event.get("repository") or {}).get("full_name") != REPOSITORY:
        raise ValueError("Wrong repository")
    if event.get("ref") != "refs/heads/remotion-requests":
        raise ValueError("Wrong request branch")
    if (event.get("sender") or {}).get("login") != OWNER:
        raise ValueError("Only owner may submit")
    commits, head = event.get("commits"), event.get("head_commit")
    if not isinstance(commits, list) or len(commits) != 1 or not isinstance(head, dict):
        raise ValueError("Exactly one commit required")
    if not str(head.get("message", "")).startswith("remotion-video: "):
        raise ValueError("Missing request commit prefix")
    sha = event.get("after")
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Invalid commit identifier")
    if head.get("id") not in (None, sha):
        raise ValueError("Event and commit SHA mismatch")
    subprocess.run(["git", "fetch", "--no-tags", "--depth=2", "origin", sha],
                   cwd=root, check=True, capture_output=True)
    parents = subprocess.run(["git", "rev-list", "--parents", "-n", "1", sha],
                             cwd=root, check=True, capture_output=True, text=True).stdout.split()
    if len(parents) != 2:
        raise ValueError("Exactly one commit parent required")
    diff = subprocess.run(["git", "diff", "--name-status", parents[1], sha],
                          cwd=root, check=True, capture_output=True, text=True).stdout.splitlines()
    if len(diff) != 1 or not diff[0].startswith("A\t"):
        raise ValueError("Exactly one added request file required")
    rel = diff[0].split("\t", 1)[1]
    if not re.fullmatch(PATH_PATTERN, rel):
        raise ValueError("Invalid request path")
    res = subprocess.run(["git", "show", sha + ":" + rel],
                         cwd=root, check=True, capture_output=True)
    if len(res.stdout) > 4500:
        raise ValueError("Request file too large")
    return validate_spec(json.loads(res.stdout.decode("utf-8")))


def write_files(spec: dict, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    render_props = {key: spec[key] for key in ("title", "subtitle", "background", "accent", "scenes", "kind")}
    render_props["hasVoice"] = False
    (destination / "props.json").write_text(json.dumps(render_props, ensure_ascii=False), encoding="utf-8")
    (destination / "duration.txt").write_text(str(spec["seconds"] * 30), encoding="utf-8")
    (destination / "claude-enabled.txt").write_text(str(spec["use_claude"]).lower(), encoding="utf-8")
    storyboard = ("Keep the five scenes in order: ordinary rainy home; emergency TV alert; zombies through the window; violent knocks on the door; grab a bag before deciding. " if spec["kind"] == "zombie-episode-1" else "")
    prompt = (
        "Return ONLY one JSON array of exactly 5 objects each with exactly heading and caption. " if spec["kind"] == "zombie-episode-1" else "Return ONLY one JSON array of 1 to 5 objects each with exactly heading and caption. "
    ) + (
        storyboard + 
        "Headings <=36 characters, captions <=90 characters, no markdown or commentary. "
        "Write concise, attractive, Spanish vertical-video motion graphic scenes. "
        "Do not include websites, links, executable text or markdown. "
        "Creative brief: " + (spec["prompt"] or spec["title"] + " - " + spec["subtitle"])
    )
    (destination / "claude-prompt.txt").write_text(prompt, encoding="utf-8")


def parse_claude_scene_text(response: str) -> list:
    """Decode JSON even when a free model adds fences or trailing commentary.

    No code execution or eval: only the first valid JSON array or scenes envelope
    is accepted, capped by the strict schema checks below.
    """
    if len(response.encode("utf-8")) > 5000:
        raise ValueError("Claude response too long")
    decoder = json.JSONDecoder()
    candidates = [response.strip()]
    for marker in ("[", "{"):
        pos = response.find(marker)
        if pos >= 0:
            candidates.append(response[pos:])
    for candidate in candidates:
        try:
            data, _ = decoder.raw_decode(candidate.lstrip())
        except json.JSONDecodeError:
            continue
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and isinstance(data.get("scenes"), list):
            return data["scenes"]
    # Some free models emit consecutive JSON objects rather than an array.
    items = []
    cursor = response.strip()
    while cursor and len(items) < 6:
        cursor = cursor.lstrip(" \r\n\t,")
        if cursor.startswith("```"):
            break
        try:
            obj, offset = decoder.raw_decode(cursor)
        except json.JSONDecodeError:
            break
        if not isinstance(obj, dict):
            break
        items.append(obj)
        cursor = cursor[offset:]
    if len(items) >= 3:
        return items
    raise ValueError("Claude scene JSON could not be parsed")


def apply_claude(response: str, destination: Path) -> None:
    scenes = parse_claude_scene_text(response)
    p = destination / "props.json"
    props = json.loads(p.read_text(encoding="utf-8"))
    expected = 5 if props.get("kind") == "zombie-episode-1" else None
    if not isinstance(scenes, list) or not 1 <= len(scenes) <= 6 or (expected and len(scenes) < 3):
        raise ValueError("Claude must return at least three valid storyboard scenes")
    out = []
    for item in scenes[:5]:
        if not isinstance(item, dict) or set(item) != {"heading", "caption"}:
            raise ValueError("Claude scene schema invalid")
        out.append({"heading": limited_text(item["heading"], 36),
                    "caption": limited_text(item["caption"], 90, required=False)})
    contributed = len(out)
    if expected and len(out) < expected:
        originals = props.get("scenes", [])
        if len(originals) < expected:
            raise ValueError("Missing owner-approved scenes for completion")
        out.extend(originals[len(out):expected])
    props["scenes"] = out
    p.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    print("CLAUDE_SCENES_USED:", contributed, "total scenes:", len(out))


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "prepare":
        root = Path.cwd()
        event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
        write_files(load_authorized_request(event, root), Path(os.environ["RUNNER_TEMP"]) / "remotion-video")
    elif mode == "offline":
        spec = validate_spec(json.loads(Path(sys.argv[2]).read_text(encoding="utf-8")))
        write_files(spec, Path(sys.argv[3]))
    elif mode == "apply-claude":
        apply_claude(Path(sys.argv[2]).read_text(encoding="utf-8"), Path(sys.argv[3]))
    else:
        raise ValueError("Usage: prepare | offline input.json directory | apply-claude output.txt directory")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, UnicodeError, subprocess.CalledProcessError,
            json.JSONDecodeError) as exc:
        print("Video request blocked: " + str(exc)[:150], file=sys.stderr)
        sys.exit(1)
