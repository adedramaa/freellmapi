#!/usr/bin/env python3
"""Create the Argentina sticker with the official DesignCraft command-line engine.
All 2-D artwork is pasted as independently editable DesignCraft paths/groups.
No raster graphics are placed in the document.
"""
import json
import pathlib
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

source=pathlib.Path(sys.argv[1]).resolve()
out=pathlib.Path(sys.argv[2]).resolve()
out.mkdir(parents=True,exist_ok=True)
svg=source.read_text(encoding="utf-8")
root=ET.fromstring(svg)
if not root.tag.endswith("svg"):
    raise SystemExit("Input is not SVG")
if "<image" in svg or "data:image" in svg:
    raise SystemExit("Raster images are prohibited in this editable vector design")
if len(svg)<35000 or svg.count("<path")<140:
    raise SystemExit("SVG shapes missing: refuse incomplete vector art")
print("Input SVG",len(svg),"characters;",svg.count("<path"),"path elements")

steps=[
 ("file.new",{"width":615,"height":615,"pages":1,"margins":0}),
 ("edit.pasteSvg",{"svg":svg,"at":[307.5,307.5]}),
]
script=out/"source_designcraft.dcs"
script.write_text("\n".join(k+" "+json.dumps(v,ensure_ascii=False,separators=(",",":")) for k,v in steps)+"\n",encoding="utf-8")
cmd=["designcraft-cli","script",str(script),
     "--save",str(out/"Argentina_Reorganizada.designcraft"),
     "--export",str(out/"Argentina_DesignCraft.png"),
     "--export",str(out/"Argentina_DesignCraft.pdf")]
print("Running official DesignCraft:",cmd[0],cmd[1])
process=subprocess.run(cmd,text=True,capture_output=True,timeout=330)
log=(process.stdout+"\n"+process.stderr)
(out/"designcraft-command-log.txt").write_text(log[-30000:],encoding="utf-8")
print("DesignCraft exit:",process.returncode)
print(log[-5500:])
if process.returncode!=0:
    raise SystemExit("DesignCraft failed, see command log")
files=["Argentina_Reorganizada.designcraft","Argentina_DesignCraft.png","Argentina_DesignCraft.pdf"]
for name in files:
    p=out/name
    if not p.exists() or p.stat().st_size<1000:
        raise SystemExit("DesignCraft didn't export "+name)
doc=(out/files[0]).read_text(encoding="utf-8",errors="replace")
# Native document must have paths, not just an image frame or linked bitmap.
shape_hits=len(re.findall(r'["\\u0027]?[Pp]ath["\\u0027]?',doc))
art_objects=len(re.findall(r'"shape"\s*:',doc))
image_refs=len(re.findall(r'"(?:image|Image|imageId|linkedFile|imageData)"\s*:',doc))
print("Native path references",shape_hits,"shape keys",art_objects,"raster refs",image_refs)
if art_objects < 100:
    raise SystemExit("Native file does not contain 100+ editable elements; refuse raster-only artifact")
metadata={"status":"SUCCESS","engine":"Official ArtCraft DesignCraft",
    "version":"0.17.2","svg_path_count":svg.count("<path"),
    "native_shape_keys":art_objects,"native_path_references":shape_hits,
    "source_image_embedded":False,
    "exported_files":{name:(out/name).stat().st_size for name in files}}
(out/"verified-editability.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
print("PASS",json.dumps(metadata))
