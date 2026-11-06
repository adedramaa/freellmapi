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
import zipfile
from collections import Counter
# .designcraft is a native ZIP package (not a flat JSON document).
with zipfile.ZipFile(out/files[0]) as package:
    required={"mimetype","meta.json","document.json"}
    if not required.issubset(package.namelist()):
        raise SystemExit("Malformed native DesignCraft package")
    designcraft_doc=json.loads(package.read("document.json"))
shape_counts=Counter()
def walk(node):
    if isinstance(node,dict):
        if "shape" in node and isinstance(node["shape"],str):
            shape_counts[node["shape"]]+=1
        for value in node.values():walk(value)
    elif isinstance(node,list):
        for value in node:walk(value)
walk(designcraft_doc)
vector_shapes=shape_counts["path"]+shape_counts["graphicLine"]
image_assets=len(designcraft_doc.get("assets",[]))
print("Native DesignCraft objects:",dict(shape_counts),"embedded assets:",image_assets)
if vector_shapes<100 or shape_counts["group"]<5 or image_assets:
    raise SystemExit("Native file failed the editable-vectors-only check")
metadata={"status":"SUCCESS","engine":"Official ArtCraft DesignCraft",
    "version":"0.17.2","svg_path_count":svg.count("<path"),
    "native_vector_shapes":vector_shapes,"native_groups":shape_counts["group"],"embedded_assets":image_assets,
    "source_image_embedded":False,
    "exported_files":{name:(out/name).stat().st_size for name in files}}
(out/"verified-editability.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
print("PASS",json.dumps(metadata))
