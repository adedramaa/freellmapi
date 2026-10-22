#!/usr/bin/env python3
"""Never execute model output: parse JSON and validate two short lines."""
import json
import re
import sys
from pathlib import Path

DEFAULT={"lines":["¡Hola! Hoy probamos una fábrica de videos.","Mi voz es gratis y puedo moverme."]}
source,target=map(Path,sys.argv[1:3])
try:
    raw=source.read_text(encoding="utf-8")
    match=re.search(r"\{[\s\S]*\}",raw)
    if not match: raise ValueError("Claude no devolvio JSON")
    proposed=json.loads(match.group(0))["lines"]
    if not isinstance(proposed,list) or len(proposed)!=2 or not all(isinstance(s,str) and 8<=len(s)<=90 and len(s.split())<=8 and "\n" not in s for s in proposed):
        raise ValueError("Longitud o estructura incorrecta")
    result={"lines":proposed}
    print("GUION_CLAUDE=validado")
except (OSError,KeyError,ValueError,TypeError) as error:
    result=DEFAULT
    print("GUION_CLAUDE=fallback_gratuito; causa:",str(error)[:160])
target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
