#!/usr/bin/env python3
"""16 agentes de Claude Code para una serie original de micro-novelas de misterio.
No ejecuta el texto del modelo como codigo ni promete audiencia simulada real.
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, time
from pathlib import Path

ROLES=[
 ("idea_1","Propon un comienzo inquietante con causa y efecto."),
 ("idea_2","Propone un misterio con una pista material verificable."),
 ("idea_3","Aumenta tension sin agregar sucesos sobrenaturales."),
 ("idea_4","Haz memorables las decisiones de Vera."),
 ("idea_5","Siembra una duda que sostenga toda la temporada."),
 ("jurado","Selecciona las ideas mas coherentes, evita giros arbitrarios."),
 ("lector_1","Critica el inicio como lector impaciente de novelas de misterio."),
 ("lector_2","Busca pistas confusas o imposibles de seguir."),
 ("lector_3","Evalua si la revelacion es justa para el lector."),
 ("lector_4","Detecta dialogos artificiales o tecnicismos."),
 ("lector_5","Detecta contradicciones de lugar, tiempo, edad o nombres."),
 ("editor_1","Depura frases y asegura ritmo de suspense."),
 ("editor_2","Asegura continuidad del misterio central."),
 ("editor_3","Haz una ultima correccion de causalidad y pistas."),
 ("editor_4","Revisa lenguaje latinoamericano natural, sin voseo."),
 ("analista","Elige un final abierto potente sin inventar metricas."),
]
assert len(ROLES)==16
DEFAULT=[
 "A las tres y diecisiete, Vera despertó.",
 "Su teléfono mostraba una llamada perdida.",
 "Venía del número de su hermano.",
 "Pero Julián llevaba seis años desaparecido.",
 "Encontró un mensaje de apenas siete segundos.",
 "En la grabación escuchó su propia voz.",
 "Decía: nunca abras el cajón inferior.",
 "Vera miró hacia el escritorio vacío.",
 "El cajón ya estaba abierto.",
 "Dentro encontró una fotografía fechada mañana.",
 "La fotografía mostraba su habitación vacía.",
 "Alguien golpeó tres veces desde el armario.",
]
BIBLE={
 "series":"EL ARCHIVO DE LAS 03:17",
 "genre":"novela de misterio psicologico y suspense realista, serializada",
 "premise":"Vera recibe llamadas que parecen involucrar a su hermano Julian desaparecido hace seis anos; alguien manipula grabaciones, documentos y horarios.",
 "canon":["Vera es la protagonista e investiga.","Julian es su hermano desaparecido hace seis anos.","Nunca confirmar hechos sobrenaturales; cada pista admite explicacion humana.","No revelar al responsable en el primer episodio."],
 "continuity":["Capitulo 1: la llamada a las 03:17, aviso del cajon, fotografia fechada manana."],
}
def parse_story(value:str, length:int=12):
 dec=json.JSONDecoder()
 for match in re.finditer(r"\\{",value):
  try: obj,_=dec.raw_decode(value[match.start():])
  except ValueError: continue
  if not isinstance(obj,dict): continue
  lines=obj.get("lines")
  if not isinstance(lines,list) or len(lines)!=length: continue
  if not all(isinstance(s,str) and 8<=len(s.strip())<=85 and len(s.split())<=8 and "\n" not in s for s in lines): continue
  title=obj.get("title","La llamada de mañana")
  if not isinstance(title,str) or not 5<=len(title)<=90: title="La llamada de mañana"
  # Canon must survive all revisions. Never let an agent move the protagonist's identity.
  combined=" ".join(lines).casefold()
  if "vera" not in combined or "juli" not in combined: continue
  return {"title":title,"lines":[s.strip() for s in lines]}
 return None

def model_call(role,task,req,previous,idea_history):
 topic=req["topic"]
 episode=req["episode"]
 instructions=("Eres parte de una sala editorial profesional de NOVELAS de MISTERIO. "
 "Suspense psicologico REALISTA, no humor, no objetos parlantes, no ciencia ficcion. "
 "Solo dos personajes nombrados, Vera y su hermano Julian, y un secreto. "
 "Aparece una pista nueva y el ultimo fragmento termina en cliffhanger sin resolver la temporada. "
 "No inventes metricas ni opiniones de espectadores reales. "
 "Devuelve SOLO JSON con title y lines. lines = exactamente 12 FRASES breves de 8 a 85 caracteres; maximo 8 PALABRAS por frase, SIN enumeraciones. "
 "La primera debe enganchar inmediatamente. La frase final debe provocar una pregunta irresistible. "
 "El guion debe mencionar Vera y Julian. Todo dialogo en español natural de Latinoamerica, sin voseo. "
 "Mantén las pistas cronologicas y los nombres; evita repetir oraciones iguales. "
 f"SERIE: {BIBLE['series']}. CANON: {json.dumps(BIBLE['canon'],ensure_ascii=False)}. "
 f"CAPITULO: {episode}. IDEA: {topic}. FUNCION DE ESTE AGENTE: {role} - {task}. "
 f"VERSION ACTUAL: {json.dumps(previous,ensure_ascii=False)}. "
 f"ANTERIORES PROPUESTAS: {json.dumps(idea_history[-2:],ensure_ascii=False)}. "
 'FORMA: {"title":"La llamada de mañana","lines":["Vera despertó cuando sonó el teléfono.","Su hermano Julián había desaparecido hace años.", "... hasta tener EXACTAMENTE 12 frases"]}')
 p=subprocess.run(["claude","--bare","-p",instructions,"--model","sonnet","--max-turns","2",
     "--tools","","--permission-mode","dontAsk","--strict-mcp-config","--disable-slash-commands",
     "--no-session-persistence","--output-format","text"],capture_output=True,text=True,timeout=95)
 if p.returncode:
  msg=(p.stderr+" "+p.stdout).lower()
  reason="rate_or_quota" if any(z in msg for z in ("429","rate limit","quota")) else "cli_"+str(p.returncode)
  raise RuntimeError(reason)
 story=parse_story(p.stdout)
 if story is None: raise ValueError("Esquema o continuidad invalida")
 return story

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument("--request",required=True,type=Path)
 parser.add_argument("--out",required=True,type=Path)
 args=parser.parse_args()
 req=json.loads(args.request.read_text(encoding="utf-8"))
 if req.get("genre")!="misterio": raise ValueError("genre debe ser misterio")
 if not isinstance(req.get("topic"),str) or not 6<=len(req["topic"])<=190 or "\n" in req["topic"]:
  raise ValueError("Tema fuera de rango")
 if req.get("episode")!=1: raise ValueError("La temporada piloto solo admite episodio 1 hasta aprobar continuidad")
 role_mode=str(req.get("agents",1))
 if role_mode not in ("1","16"):raise ValueError("agents requiere 1 o 16")
 roles=ROLES if role_mode=="16" else [("guionista","Crear misterio original coherente con las pistas")]
 state={"title":"La llamada de mañana","lines":DEFAULT[:]}
 records=[];ideas=[];faults=0
 for role,task in roles:
  if not os.getenv("ANTHROPIC_AUTH_TOKEN"):
   records.append({"role":role,"status":"no_gateway_token"});break
  try:
   result=model_call(role,task,req,state,ideas)
  except (RuntimeError,ValueError,subprocess.TimeoutExpired) as e:
   records.append({"role":role,"status":"failure","error":str(e)[:90]})
   faults+=1
   print(role+": fallo",flush=True)
   if faults>=3: break
   time.sleep(12)
   continue
  state=result;ideas.append(result)
  records.append({"role":role,"status":"success"})
  faults=0
  print(role+": historia validada",flush=True)
  if len(roles)>1 and role!=roles[-1][0]:time.sleep(20)
 args.out.parent.mkdir(parents=True,exist_ok=True)
 report={"requested":len(roles),"successes":sum(x["status"]=="success" for x in records),
         "attempts":len(records),"fallback":len(ideas)==0,"roles":records}
 args.out.write_text(json.dumps({**state,"series":BIBLE["series"],"part":1},ensure_ascii=False,indent=2),encoding="utf-8")
 args.out.with_name("mystery_bible.json").write_text(json.dumps(BIBLE,ensure_ascii=False,indent=2),encoding="utf-8")
 args.out.with_name("mystery_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
 print("MYSTERY_ROLES="+str(report["successes"])+"/"+str(report["requested"]),flush=True)
 print("MYSTERY_TITLE="+state["title"],flush=True)

if __name__=="__main__":main()
