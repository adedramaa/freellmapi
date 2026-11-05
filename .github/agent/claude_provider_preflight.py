"""Preflight provider availability before starting Claude Code CLI.

Uses existing FreeLLMAPI unified key; prints only allowlisted status metadata.
Never prints secrets, response bodies, provider errors or user content.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

ENDPOINT = "https://adedrama-freellmapi.onrender.com/v1/providers"
TARGET = "groq"


def check() -> int:
    key = os.environ.get("FREELLMAPI_API_KEY", "")
    if not key:
        print("Claude bridge preflight: unified key is missing.")
        return 1
    request = urllib.request.Request(
        ENDPOINT, headers={"Authorization": "Bearer " + key, "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status != 200:
                print("Claude bridge preflight: provider status unavailable.")
                return 1
            # Size cap protects CI logs and memory. No raw data printed.
            payload = json.loads(response.read(32769))
    except urllib.error.HTTPError as exc:
        print(f"Claude bridge preflight: status endpoint returned HTTP {exc.code}.")
        return 1
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
        print("Claude bridge preflight: unable to check provider status.")
        return 1

    if not isinstance(payload, dict) or not isinstance(payload.get("providers"), list):
        print("Claude bridge preflight: invalid provider status format.")
        return 1
    matches = [entry for entry in payload["providers"]
               if isinstance(entry, dict) and entry.get("platform") == TARGET]
    if len(matches) != 1:
        print("Claude bridge preflight: no enabled Groq key found.")
        return 1
    provider = matches[0]
    state = provider.get("status")
    if state == "rate_limited":
        resume = provider.get("resume_at")
        if isinstance(resume, str):
            try:
                instant = datetime.fromisoformat(resume.replace("Z", "+00:00"))
                if instant.tzinfo is not None:
                    print("Claude bridge preflight: Groq cooling down until "
                          + instant.astimezone(timezone.utc).isoformat() + ".")
                else:
                    print("Claude bridge preflight: Groq in cooldown.")
            except ValueError:
                print("Claude bridge preflight: Groq in cooldown.")
        else:
            print("Claude bridge preflight: Groq in cooldown.")
        return 1
    if state != "healthy":
        print("Claude bridge preflight: Groq not healthy (state="
              + str(state if state in {"unknown", "invalid"} else "unavailable") + ").")
        return 1
    print("Claude bridge preflight: Groq healthy; proceeding with constrained Claude Code.")
    return 0


if __name__ == "__main__":
    sys.exit(check())
