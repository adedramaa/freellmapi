"""16 roles independent Claude Code requests via free FreeLLMAPI. No purchases."""
from __future__ import annotations
import argparse, json, os, subprocess, time
from pathlib import Path

DEFAULT=["¡Hola! Hoy probamos una fábrica de videos.","Mi voz es gratis y puedo moverme."]
ROLES=(
 [(f"creativo_{i}",v) for i,v in enumerate(
  ["humor cotidiano","comedia visual","remate inesperado","curiosidad tecnológica","ritmo divertido"],1)]
 + [("jurado","elegir la mejor idea y el mejor gancho")]
 + [(f"espectador_{i}",v) for i,v in enumerate(
  ["atención en el primer segundo","espontaneidad","claridad para principiantes",
   "capacidad de compartirlo","inteligibilidad sin subtítulos"],1)]
 + [(f"revisor_{i}",v) for i,v in enumerate(
  ["mejorar humor","revisar claridad","evitar voz robótica","eliminar redundancias"],1)]
 + [("analista","elegir versión final sin inventar métricas")]
)
assert len(ROLES)==16

def parse_lines(output):
    start,end=output.find("{"),output.rfind("}")
    if start<0 or end<=start: return None
    try: obj=json.loads(output[start:end+1]); lines=obj["lines"]
    except (ValueError,KeyError,TypeError): return None
    if not isinstance(lines,list) or len(lines)!=2: return None
    if not all(isinstance(s,str) and 8<=len(s)<=75 and len(s.split())<=8 and "\n" not in s for s in lines): return None
    return [v.strip() for v in lines]

def ask(role,focus,topic,current,options):
    prompt=("Eres agente de guion para reels 3D: una taza con cara habla a cámara. "
      "Español latinoamericano, rápido y conversacional, con humor inteligente, sin voseo. "
      "No inventes resultados, promesas de viralidad ni cifras. "
      "Responde SOLO JSON con la clave lines y DOS FRASES de 8 a 75 caracteres, máximo 8 PALABRAS cada una. "
      f"TEMA: {topic}. ROL: {role}; OBJETIVO: {focus}. "
      f"BORRADOR ACTUAL: {json.dumps(current,ensure_ascii=False)}. "
      f"IDEAS PREVIAS: {json.dumps(options[-5:],ensure_ascii=False)}. "
      'FORMATO: {"lines":["Una frase breve y entretenida.","Otro remate breve y natural."]}')
    result=subprocess.run(["claude","--bare","-p",prompt,"--model","sonnet","--max-turns","2",
       "--tools","","--permission-mode","dontAsk","--strict-mcp-config",
       "--disable-slash-commands","--no-session-persistence","--output-format","text"],
       capture_output=True,text=True,timeout=75,check=False)
    if result.returncode: raise RuntimeError("Claude CLI error "+str(result.returncode))
    lines=parse_lines(result.stdout)
    if not lines: raise ValueError("Salida del agente no valida (JSON/esquema)")
    return lines

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--request",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    req=json.loads(args.request.read_text(encoding="utf-8"))
    topic=req.get("topic","Una taza que prueba una fábrica de videos")
    if not isinstance(topic,str) or not 5<=len(topic)<=160 or "\n" in topic:
        raise ValueError("Tema invalido, 5-160 caracteres")
    mode=str(req.get("agents","1"))
    if mode not in ("1","16"): raise ValueError("agents admite 1 o 16")
    roles=[("guionista","proponer un guion corto memorable")] if mode=="1" else ROLES
    current,options,report=DEFAULT[:],[],[]
    if not os.getenv("ANTHROPIC_AUTH_TOKEN"):
        report.append({"role":"gateway","status":"sin_token"}); roles=[]
    consecutive=0
    for role,focus in roles:
        started=time.monotonic()
        try:
            lines=ask(role,focus,topic,current,options)
            current=lines;options.append(lines);consecutive=0
            report.append({"role":role,"status":"success","seconds":round(time.monotonic()-started,1)})
            print(role+": JSON valido",flush=True)
        except (RuntimeError,ValueError,subprocess.TimeoutExpired) as exc:
            consecutive+=1
            report.append({"role":role,"status":"failure","error":str(exc)[:120],
                           "seconds":round(time.monotonic()-started,1)})
            print(role+": fallo, conserva texto anterior",flush=True)
            if consecutive>=3: break
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps({"lines":current},ensure_ascii=False,indent=2),encoding="utf-8")
    status={"requested_roles":len(roles),"attempted_roles":len([x for x in report if x["role"]!="gateway"]),
            "completed_roles":sum(x["status"]=="success" for x in report),
            "used_default":not bool(options),"topic":topic,"roles":report}
    args.out.with_name("agents_report.json").write_text(
        json.dumps(status,ensure_ascii=False,indent=2),encoding="utf-8")
    print("AGENTS_COMPLETED="+str(status["completed_roles"])+"/"+str(len(roles)),flush=True)
    print("FINAL_SCRIPT="+json.dumps(current,ensure_ascii=False),flush=True)

if __name__=="__main__": main()
