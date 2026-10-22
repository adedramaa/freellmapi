#!/usr/bin/env python3
"""Exact Spanish subtitles for the approved original 32.8s voiceover (not model-generated)."""
from pathlib import Path
EVENTS=[
 (0.12,1.44,"A las tres y"),
 (1.44,2.77,"diecisiete, Vera despertó."),
 (2.77,4.24,"Su teléfono mostraba"),
 (4.24,5.71,"una llamada perdida."),
 (5.71,6.77,"Venía del número"),
 (6.77,7.84,"de su hermano."),
 (7.84,9.33,"Pero Julián llevaba"),
 (9.33,10.83,"seis años desaparecido."),
 (10.83,12.26,"Encontró un mensaje de"),
 (12.26,13.69,"apenas siete segundos."),
 (13.69,14.96,"En la grabación escuchó"),
 (14.96,16.24,"su propia voz."),
 (16.24,17.52,"Decía: nunca abras"),
 (17.52,18.81,"el cajón inferior."),
 (18.81,20.06,"Vera miró hacia"),
 (20.06,21.31,"el escritorio vacío."),
 (21.31,22.36,"El cajón ya"),
 (22.36,23.42,"estaba abierto."),
 (23.42,24.94,"Dentro encontró una"),
 (24.94,26.46,"fotografía fechada mañana."),
 (26.46,27.93,"La fotografía mostraba"),
 (27.93,29.40,"su habitación vacía."),
 (29.40,30.86,"Alguien golpeó tres veces"),
 (30.86,32.32,"desde el armario.")
]
def fmt(t):
 h=int(t//3600);m=int((t%3600)//60);s=int(t%60);cs=int(round((t%1)*100))
 return f"{h}:{m:02d}:{s:02d}.{cs:02d}"
def make(output):
 header="""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Narrador,DejaVu Sans,54,&H00FFFFFF,&H00FFFFFF,&H00101522,&H90000000,1,0,0,0,100,100,0,0,1,3.4,1,2,70,70,220,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
 assert len(EVENTS)==24
 output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
 content=header+"".join(f"Dialogue: 0,{fmt(s)},{fmt(e)},Narrador,,0,0,0,,{text}\n" for s,e,text in EVENTS)
 output.write_text(content,encoding="utf-8")
 return output
if __name__=="__main__":
 import sys;print(make(sys.argv[1]))
