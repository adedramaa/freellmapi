"""Create royalty-free procedural suspense ambience and optional neural Spanish speech.

No files or requests are supplied as executable code. If speech fails, the
video renders with subtitles and ambience; it must never claim it has narration.
"""
from __future__ import annotations

import asyncio
import json
import math
import os
from pathlib import Path
import random
import struct
import sys
import wave

SCRIPTS = [
    "Estaba solo en casa. Todo parecía una tarde normal.",
    "La televisión lanzó una alerta: ¡quédense adentro! ¡No abran las puertas!",
    "Miré por la ventana. Gente corriendo, coches chocados... y gritos.",
    "Entonces lo vi. Mi vecino perseguía a una mujer. Ya no era humano.",
    "Tres golpes sacudieron la puerta. Alguien quería entrar. O algo.",
    "Tomé agua y una mochila. No tenía tiempo para pensar.",
    "Tú decides. A: me encierro y resisto. B: escapo por atrás. ¡Comenta A o B para decidir la siguiente parte!",
]
VOICES = ["es-VE-SebastianNeural", "es-MX-JorgeNeural", "es-ES-AlvaroNeural"]


def make_ambience(dest: Path, seconds: int = 40) -> None:
    """Create mixed eerie drones, low siren and three knocks, all synthesized."""
    hz = 22050
    rnd = random.Random(41)
    ph = 0.0
    dest.parent.mkdir(parents=True, exist_ok=True)
    # 44.1KB/s mono, no licensing dependencies.
    with wave.open(str(dest), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(hz)
        buf = bytearray()
        for n in range(seconds * hz):
            t = n / hz
            # Low ominous drone with tremolo and distant siren after alert.
            low = math.sin(2 * math.pi * 52 * t) * (0.18 + 0.05 * math.sin(t * .48))
            low += math.sin(2 * math.pi * 78.5 * t) * 0.09
            siren = math.sin(2 * math.pi * (390 * t + 52 * math.sin(t * 1.7))) * 0.04 if 5 < t < 28 else 0
            # Radio static, rain-like noise and knocking at the door
            rain = (rnd.random() * 2 - 1) * 0.048
            knock = 0.0
            for hit in (22.4, 22.85, 23.3, 25.3):
                dt = t - hit
                if 0 <= dt < .30:
                    knock += math.sin(2 * math.pi * 63 * dt) * math.exp(-dt * 20) * .75
            pulse = math.sin(2 * math.pi * (1.2 if t < 31 else 1.8) * t) * (0.055 if t > 28 else 0)
            signal = max(-.92, min(.92, low + siren + rain + knock + pulse))
            buf += struct.pack("<h", int(signal * 32767))
        audio.writeframes(buf)


async def create_voice(target: Path) -> bool:
    try:
        import edge_tts
    except ImportError:
        print("Narration unavailable: edge-tts not installed.")
        return False
    for voice in VOICES:
        try:
            for n, text in enumerate(SCRIPTS):
                file = target / ("voice-" + str(n) + ".mp3")
                await edge_tts.Communicate(text=text, voice=voice, rate="+9%", volume="+0%").save(str(file))
                if not file.exists() or file.stat().st_size < 500:
                    raise RuntimeError("Empty voice file")
            print("PASS: neural narration created in Spanish with voice", voice)
            return True
        except Exception as exc:
            print("Voice server unavailable for", voice, str(exc)[:70])
            for n in range(len(SCRIPTS)):
                (target / ("voice-" + str(n) + ".mp3")).unlink(missing_ok=True)
    return False


def run() -> None:
    props = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    if not props.is_file():
        raise ValueError("Missing validated props")
    data = json.loads(props.read_text(encoding="utf-8"))
    if data.get("kind") != "zombie-episode-1":
        return
    output.mkdir(parents=True, exist_ok=True)
    make_ambience(output / "zombie-ambience.wav")
    success = asyncio.run(create_voice(output))
    data["hasVoice"] = success
    props.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print("Zombie audio preparation complete; voice:", "YES" if success else "NO")


if __name__ == "__main__":
    run()
