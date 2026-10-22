#!/usr/bin/env python3
"""Uso personal de La Fabrica: cambia ElevenLabs por Kokoro local y usa su Blender real."""
from __future__ import annotations
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

def words_by_duration(text, duration):
    pieces=text.split()
    weights=[max(1,len(p.strip('¡!¿?.,;:'))) for p in pieces]
    total=sum(weights); now=.035; usable=max(.15,duration-.10); out=[]
    for word,w in zip(pieces,weights):
        end=min(duration,now+w/total*usable)
        out.append({"text":word,"start":round(now,3),"end":round(end,3)})
        now=end
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--factory",required=True,type=Path)
    ap.add_argument("--lines",required=True,type=Path)
    ap.add_argument("--voice",choices=["em_alex","ef_dora","em_santa"],default="em_alex")
    args=ap.parse_args()
    lines=json.loads(args.lines.read_text(encoding="utf-8"))["lines"]
    if not isinstance(lines,list) or len(lines)!=2 or any(not isinstance(t,str) or not 8<=len(t)<=90 for t in lines):
        raise ValueError("Se requieren dos frases breves y validadas")
    factory=args.factory.resolve()
    sys.path.insert(0,str(factory))
    import numpy as np
    import soundfile as sf
    from kokoro import KPipeline
    from reels import smoke,system
    from reels.schema import Episode
    from reels import build as engine
    episode_dir=smoke.prepare()
    data=json.loads((episode_dir/"script.json").read_text(encoding="utf-8"))
    for beat,text in zip((x for x in data["beats"] if x["line"]),lines):
        beat["line"]=text
    data["title"]="La Fabrica gratuita: demo 3D con Kokoro"
    (episode_dir/"script.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    episode=Episode.model_validate(data)
    print("Sintetizando voz natural en espanol SIN ElevenLabs",flush=True)
    pipeline=KPipeline(lang_code="e")
    for beat in (b for b in episode.beats if b.line):
        base=episode_dir/"audio"/f"beat_{beat.id:02d}"
        parts=[np.asarray(audio,dtype=np.float32).reshape(-1) for _,_,audio in pipeline(beat.line,voice=args.voice,speed=1.05)]
        if not parts: raise RuntimeError("Kokoro no devolvio audio")
        audio=np.concatenate(parts)
        if len(audio)<2400: raise RuntimeError("Audio demasiado corto")
        sf.write(str(base.with_suffix(".wav")),audio,24000,subtype="PCM_16")
        subprocess.run([system.ffmpeg(),"-y","-v","error","-i",str(base.with_suffix(".wav")),"-codec:a","libmp3lame","-q:a","3",str(base.with_suffix(".mp3"))],check=True)
        seconds=len(audio)/24000
        meta={"text":beat.line,"heard":None,"voice_engine":"kokoro-local","gap_before":0.0,"words":words_by_duration(beat.line,seconds)}
        base.with_suffix(".json").write_text(json.dumps(meta,ensure_ascii=False),encoding="utf-8")
        print(f"Voz {beat.id}: {seconds:.1f}s",flush=True)
    os.environ["REELS_RENDER_ENGINE"]="cycles"
    print("Sincronizando labios con Rhubarb y creando escena Blender",flush=True)
    engine.build(episode)
    renderer=factory/"blender"/"render.py"
    original=renderer.read_text(encoding="utf-8")
    marker="scene.cycles.use_denoising = False"
    if marker not in original: raise RuntimeError("No se encontró opción de denoise de La Fabrica")
    renderer.write_text(original.replace(marker,"scene.cycles.use_denoising = True"),encoding="utf-8")
    print("Renderizando Blender CPU en calidad draft con denoise (6 samples)",flush=True)
    engine.render(episode.slug,"draft")
    final=engine.compose(episode.slug)
    out=Path(os.environ.get("GITHUB_WORKSPACE",Path.cwd()))/"fabrica_free"/"out"
    out.mkdir(parents=True,exist_ok=True)
    destination=out/"fabrica_kokoro_3d.mp4"
    shutil.copy2(final,destination)
    print("FINAL_MP4="+str(destination),flush=True)

if __name__=="__main__":
    main()
