"""Load the REAL installed official Remotion Skill into minimal Claude Code mode.

This explicitly supplies plugin skill guidance while avoiding a 413 caused by
native Skill tool context expansion through the small FreeLLMAPI gateway.
"""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
import sys


def locate_skill(root: Path, name: str) -> Path:
    base = root / ".claude" / "plugins" / "cache" / "remotion"
    candidates = sorted(base.glob(f"remotion/*/skills/{name}/SKILL.md"))
    if not candidates:
        # Older CLI cache layout, same official plugin.
        candidates = sorted(base.glob(f"*/skills/{name}/SKILL.md"))
    if not candidates:
        raise RuntimeError("Official installed Remotion Skill not found")
    return candidates[-1]


def build_prompt(home: Path, brief: str) -> tuple[str, str]:
    if not brief.strip() or len(brief) > 1600:
        raise ValueError("Video brief must be under 1600 characters")
    content = []
    digests = []
    for skill in ("remotion-best-practices", "remotion-render"):
        file = locate_skill(home, skill)
        data = file.read_text(encoding="utf-8")
        if not (data.startswith("---") and len(data) < 25000 and "remotion" in data.lower()):
            raise RuntimeError("Official Remotion plugin Skill failed validation")
        digests.append(f"{skill}={hashlib.sha256(data.encode()).hexdigest()[:16]}")
        content.append(f"=== OFFICIAL REMOTION SKILL: {skill} ===\n{data}")
    prelude = (
        "These are the actual SKILL.md files loaded from the official Remotion plugin "
        "installed on this Claude Code runner. Follow the relevant directions for "
        "Remotion timeline scenes, video vertical layout and actual MP4 rendering. "
        "Use the creative brief to draft scene copy; the controlled renderer builds "
        "video frames from its reviewed React composition. Do not run tools. "
        "Return ONLY the requested JSON array and no explanatory text.\n\n"
    )
    return prelude + "\n\n".join(content) + "\n\n=== VIDEO BRIEF ===\n" + brief, "; ".join(digests)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: remotion_skill_prompt.py BRIEF_PATH OUTPUT_PATH")
    brief = Path(sys.argv[1]).read_text(encoding="utf-8")
    assembled, sha = build_prompt(Path.home(), brief)
    Path(sys.argv[2]).write_text(assembled, encoding="utf-8")
    print("SKILL_CONTEXT_VERIFIED: plugin=remotion@remotion skills=remotion-best-practices,remotion-render sha256-prefixes=" + sha + " prompt_bytes=" + str(len(assembled.encode())))


if __name__ == "__main__":
    main()
