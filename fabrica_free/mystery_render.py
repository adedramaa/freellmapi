#!/usr/bin/env python3
"""Render a serialized original psychological mystery with La Fabrica's Blender/Remotion engine.
Claude Code is the writer; Kokoro is the actual synthesizer; Blender is the actual 3D renderer.
"""
from __future__ import annotations
import argparse, copy, json, os, shutil, subprocess, sys
from pathlib import Path

def words_by_duration(text:str,duration:float)->list[dict]:
    words=text.split()
    weights=[max(1,len(w.strip('¡!¿?.,;:'))) for w in words]
    usable=max(.12,duration-.15); total=sum(weights); t=.04; spans=[]
    for token,w in zip(words,weights):
        end=min(duration,t+usable*w/total)
        spans.append({"text":token,"start":round(t,3),"end":round(end,3)})
        t=end
    return spans

def episode_from_story(base:dict,story:dict,request:dict):
    from reels.schema import Episode
    if not isinstance(story,dict) or not isinstance(story.get("lines"),list):
        raise ValueError("Guion sin frases")
    lines=story["lines"]
    if len(lines)!=12 or not all(isinstance(v,str) and 8<=len(v)<=85 and len(v.split())<=8 for v in lines):
        raise ValueError("Misterio exige exactamente 12 frases de maximo 8 palabras")
    data=copy.deepcopy(base)
    part=request["episode"]
    if type(part) is not int or not 1<=part<=6: raise ValueError("Episodios 1 a 6")
    data.update({"slug":f"misterio-ep{part:02d}","title":story.get("title","La llamada de mañana"),
       "premise":"Vera recibe una llamada del numero de su hermano desaparecido. Investigacion de suspense.",
       "tone":"serie","series":{"name":story.get("series","EL ARCHIVO DE LAS 03:17"),"part":part,"of":6},
       "set":"escritorio_noche","hook":"LA LLAMADA DE LAS 03:17","music":None,
       "loop_hint":"Quien envio la fotografia y que significa el cajon?",
       "alt_hooks":["Su hermano desapareció. Su teléfono volvió a sonar.","La llamada provenía de alguien desaparecido."],
       "characters":["humano","voz_sola"],"reparto":{"humano":"chica"}})
    # A 3D human tells the thriller. The object acts as a silent clue, not a comedy character.
    template=next(b for b in base["beats"] if b["line"])
    cameras=("closeup_novato","over_shoulder","closeup_novato","two_shot",
             "medium_novato_low","closeup_novato","over_shoulder","closeup_novato",
             "wide_room","closeup_novato","two_shot","closeup_novato")
    actions=("idle","look_phone","idle","idle","look_phone","slump",
             "idle","idle","slump","idle","slump","idle")
    shots=[]
    for idx,line in enumerate(lines):
        b=copy.deepcopy(template)
        b.update({"id":idx+1,"speaker":"voz_sola","line":line,"camera":cameras[idx],
          "action":actions[idx],
          "emotion":"alarma" if idx in (3,5,10,11) else "confuso",
          "listener_emotion":"neutral","event":None,"sfx":[],
          "hold":0.06 if idx<11 else 0.32,"delivery":{"tags":[],"pace":"normal",
             "pause_before":0.0 if idx==0 else 0.07 if idx!=6 else 0.2,"intensity":"media"}})
        if idx==0:
            b["light"]="madrugada"
            b["ambience"]="noche"
        else:
            b["light"]=None
            b["ambience"]=None
        # Narrative evidence appears in-world on the actor's phone/laptop.
        if idx==1:
            b["camera"]="phone_screen"
            b["event"]={"type":"screen","component":"PhoneCall",
                         "props":{"contact":"Julián" if part==1 else "Número oculto",
                                  "connect_after":None}}
        if idx==8:
            b["camera"]="screen_closeup"
            b["event"]={"type":"screen","component":"SystemNotice",
                         "props":{"title":"ARCHIVO 47A" if part>1 else "MENSAJE 03:17",
                                  "text":"Última conexión registrada"}}
        if idx==10:
            b["light"]="apagon"
        shots.append(b)
    silent=copy.deepcopy(base["beats"][-1])
    silent.update({"id":len(shots)+1,"speaker":None,"line":None,
                   "camera":"negro","hold":1.3,"event":None,
                   "emotion":"alarma","listener_emotion":"neutral","action":"idle"})
    shots.append(silent)
    data["beats"]=shots
    return Episode.model_validate(data),data

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--factory",required=True,type=Path)
    a.add_argument("--story",required=True,type=Path)
    a.add_argument("--request",required=True,type=Path)
    a.add_argument("--validate-only",action="store_true")
    args=a.parse_args()
    request=json.loads(args.request.read_text(encoding="utf-8"))
    story=json.loads(args.story.read_text(encoding="utf-8"))
    quality=request.get("quality","humo")
    voice=request.get("voice","em_alex")
    if quality not in ("humo","draft"):raise ValueError("quality acepta humo o draft")
    if voice not in ("em_alex","em_santa","ef_dora"):raise ValueError("Voz Kokoro no admitida")
    project=args.factory.resolve()
    sys.path.insert(0,str(project))
    from reels import smoke,system
    from reels import build as engine
    from reels.schema import Episode
    directory=smoke.prepare()
    base=json.loads((directory/"script.json").read_text(encoding="utf-8"))
    episode,raw=episode_from_story(base,story,request)
    # The smoke fixture lives under episodes/humo. Move it to the actual story slug
    # before generating audio: timeline/lipsync always resolve paths by episode.slug.
    actual=directory.parent/episode.slug
    if actual.exists():
        shutil.rmtree(actual)
    directory.rename(actual)
    directory=actual
    (directory/"script.json").write_text(json.dumps(raw,ensure_ascii=False,indent=2),encoding="utf-8")
    if args.validate_only:
        print("EPISODIO_VALIDO="+str(len(episode.beats))+" escenas, 12 dialogos, cliffhanger",flush=True)
        return
    import numpy as np
    import soundfile as sf
    from kokoro import KPipeline
    print("VOZ_LOCAL=Kokoro (no ElevenLabs, sin suscripcion)",flush=True)
    k=KPipeline(lang_code="e")
    for beat in episode.beats:
        if not beat.line: continue
        target=directory/"audio"/f"beat_{beat.id:02d}"
        samples=[np.asarray(audio,dtype=np.float32).reshape(-1) for _gr,_ph,audio in k(beat.line,voice=voice,speed=1.02)]
        if not samples:raise RuntimeError("Sin audio para escena "+str(beat.id))
        audio=np.concatenate(samples)
        sf.write(str(target.with_suffix(".wav")),audio,24000,subtype="PCM_16")
        subprocess.run([system.ffmpeg(),"-y","-loglevel","error","-i",str(target.with_suffix(".wav")),
                        "-codec:a","libmp3lame","-q:a","3",str(target.with_suffix(".mp3"))],check=True)
        meta={"text":beat.line,"voice_engine":"kokoro-local","words":words_by_duration(beat.line,len(audio)/24000)}
        target.with_suffix(".json").write_text(json.dumps(meta,ensure_ascii=False),encoding="utf-8")
        print("ESCENA="+str(beat.id)+", AUDIO="+str(round(len(audio)/24000,2))+"s",flush=True)
    os.environ["REELS_RENDER_ENGINE"]="cycles"
    print("ESCENAS_3D=Blender, sincronizacion de labios Rhubarb",flush=True)
    engine.build(episode)
    renderer=project/"blender"/"render.py"
    source=renderer.read_text(encoding="utf-8")
    switch="scene.cycles.use_denoising = False"
    if switch not in source:raise RuntimeError("Version del renderer no soportada")
    renderer.write_text(source.replace(switch,"scene.cycles.use_denoising = True"),encoding="utf-8")
    engine.render(episode.slug,quality)
    final=engine.compose(episode.slug)
    result=Path(os.environ.get("GITHUB_WORKSPACE",Path.cwd()))/"fabrica_free"/"mystery_output"
    result.mkdir(parents=True,exist_ok=True)
    shutil.copy2(final,result/f"misterio_ep{part:02d}.mp4")
    shutil.copy2(directory/"script.json",result/"3d_scene_script.json")
    print("MISTERIO_MP4="+str(result/f"misterio_ep{part:02d}.mp4"),flush=True)

if __name__=="__main__": main()
