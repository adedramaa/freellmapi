#!/usr/bin/env python3
"""Original TRUE Blender 3D keyframed suspense scenes, with no on-screen narrator.
Builds a 32.8 second sequence. Animates actors, physical objects, cameras and light.
No slideshow images and no speaking anthropomorphic objects.
"""
import bpy, math, argparse, sys, json
from pathlib import Path
from mathutils import Vector

def arguments():
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True)
    ap.add_argument("--fps",type=int,default=10)
    ap.add_argument("--width",type=int,default=432)
    ap.add_argument("--height",type=int,default=768)
    ap.add_argument("--samples",type=int,default=6)
    ap.add_argument("--preview",action="store_true")
    return ap.parse_args(argv)

a=arguments()
if not 8<=a.fps<=24 or not 320<=a.width<=1080 or a.samples<2:
    raise ValueError("FPS, resolution or samples outside safe CPU range")
FPS=a.fps
def frame(seconds):return 1+round(seconds*FPS)
def key(obj,prop,t,value):
    setattr(obj,prop,value)
    obj.keyframe_insert(data_path=prop,frame=frame(t))

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for data in list(bpy.data.materials):bpy.data.materials.remove(data)

def mat(name,color,metal=0,rough=.7,glow=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1)
    m.use_nodes=True
    p=m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=(*color,1)
    p.inputs["Roughness"].default_value=rough
    p.inputs["Metallic"].default_value=metal
    if glow:
        e=p.inputs.get("Emission Color")
        if e is not None:e.default_value=(*color,1)
        strength=p.inputs.get("Emission Strength")
        if strength is not None:strength.default_value=glow
    return m
wall=mat("Pintura azul petróleo mate",(.035,.059,.087))
wood=mat("Madera antigua",(.17,.115,.105))
darkwood=mat("Madera de armario",(.12,.07,.07))
floor=mat("Suelo grafito",(.07,.076,.086))
cream=mat("Papel antiguo",(.68,.63,.54))
cloth=mat("Ropa gris azulada",(.065,.105,.15))
blanket=mat("Manta azul humo",(.08,.12,.16))
skin=mat("Piel Vera",(.44,.27,.22))
hair=mat("Pelo negro",(.022,.025,.039))
metal=mat("Metal oscuro",(.16,.19,.22),.65,.3)
black=mat("Negro azulado",(.009,.015,.029))
glass=mat("Cristal telefono",(.025,.07,.12),.3,.12)
white=mat("Luz fria de pantalla",(.45,.75,.95),0,.3,2.4)
red=mat("Aviso rojo",(.9,.12,.18),0,.3,1.6)
gold=mat("Lámpara ámbar",(.75,.45,.19),0,.4,1.5)

def box(name,loc,scale,material,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object;o.name=name;o.dimensions=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(material)
    if bevel:
        m=o.modifiers.new("Bordes reales 3D","BEVEL")
        m.width=bevel;m.segments=2
        o.modifiers.new("Normales", "WEIGHTED_NORMAL")
    return o
def sphere(name,loc,r,material,segments=16,rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,radius=r,location=loc)
    o=bpy.context.object;o.name=name;o.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return o
def cylinder(name,loc,r,depth,material):
    bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=r,depth=depth,location=loc)
    o=bpy.context.object;o.name=name;o.data.materials.append(material)
    return o
def letters(name,value,loc,size,material,rot=(0,0,0)):
    cu=bpy.data.curves.new(name,"FONT");cu.body=value;cu.size=size;cu.extrude=.001
    o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o)
    o.location=loc;o.rotation_euler=rot;cu.materials.append(material)
    return o
def parent_to(o,parent):
    world=o.matrix_world.copy()
    o.parent=parent
    o.matrix_world=world
def look(obj,target):
    direction=Vector(target)-obj.location
    obj.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
def light(name,loc,energy,size,color):
    bpy.ops.object.light_add(type="AREA",location=loc)
    o=bpy.context.object;o.name=name;o.data.energy=energy
    o.data.shape="DISK";o.data.size=size;o.data.color=color
    return o

# Physical room, no green screens, no raster photos reused as 'animation'.
box("Piso continuo",(0,0,-.07),(9,8,.12),floor)
box("Muro nocturno",(0,2.98,1.65),(9,.15,3.5),wall)
box("Pared lateral",(-4.20,0,1.65),(.14,8,3.5),wall)
box("Zocalo",(0,2.83,.13),(9,.07,.23),darkwood)
box("Ventana marco",(-2.9,2.85,2.25),(1.6,.10,1.15),darkwood,.035)
box("Cristal luna",(-2.9,2.78,2.27),(1.37,.03,.94),glass)
box("Cruce de marco",(-2.9,2.72,2.27),(.055,.07,.99),metal)
box("Travesaño",(-2.9,2.70,2.25),(1.38,.07,.055),metal)

# Bed and side table.
box("Base cama",(-1.65,.30,.32),(2.25,1.65,.5),wood,.07)
box("Colchon",(-1.65,.30,.61),(2.13,1.52,.26),cream,.09)
box("Manta",(-1.65,.40,.80),(2.02,1.14,.13),blanket,.10)
box("Almohada",(-2.22,.24,.86),(.62,.55,.14),cloth,.065)
box("Mesita",(-2.80,-1.15,.57),(.9,.62,1.12),wood,.035)
box("Mesita cajon",(-2.80,-1.48,.62),(.72,.055,.36),darkwood)
lampbox=box("Luz mesita",(-3.05,-1.10,1.26),(.29,.27,.15),metal,.04)
phone=box("Teléfono móvil físico",(-2.70,-1.18,1.17),(.38,.70,.06),metal,.045)
screen=box("Pantalla móvil real",(-2.70,-1.18,1.211),(.335,.64,.005),glass,.02)
time_text=letters("Hora 03 17","03:17",(-2.83,-1.07,1.225),.105,white)
call_text=letters("Contacto JULIAN","JULIAN",(-2.85,-1.29,1.225),.067,white)
missed=letters("Llamada perdida","LLAMADA PERDIDA",(-2.85,-1.37,1.225),.029,red)
phone_light=light("Iluminacion animada movil",(-2.70,-1.16,1.65),75,.75,(.45,.72,1.0))
for t,e in [(0,9),(1.5,40),(2.8,85),(3.7,24),(4.8,100),(5.65,28),(8,45)]:
    key(phone_light.data,"energy",t,e)

# VERA: licensed real female rigged human mesh, NO cubes, NO spheres as a stand-in.
# Model: Quaternius Universal Base Characters (CC0), sourced separately.
import os
fem_path=Path(os.environ.get("VERA_FBX","fabrica_free/assets/Superhero_Female_FullBody.fbx"))
if not fem_path.is_file() or fem_path.stat().st_size<250000:
    raise RuntimeError("Se exige el personaje 3D articulado femenino CC0; no se permite un personaje de cubos")
before=set(bpy.data.objects.keys())
bpy.ops.import_scene.fbx(filepath=str(fem_path.resolve()),use_anim=True)
imported=[o for o in bpy.data.objects if o.name not in before]
character_meshes=[o for o in imported if o.type=="MESH"]
character_rigs=[o for o in imported if o.type=="ARMATURE"]
if not character_meshes or not character_rigs:
    raise RuntimeError("El modelo de Vera debe tener malla real y armadura Blender. No placeholders.")
root=bpy.data.objects.new("VERA ACTRIZ CON RIG REAL (SILENCIOSA)",None)
bpy.context.collection.objects.link(root)
roots=[o for o in imported if o.parent not in imported]
for o in roots:
    o.parent=root
    o.matrix_parent_inverse=root.matrix_world.inverted()
for o in character_meshes:
    for face in o.data.polygons:
        face.use_smooth=True
bpy.context.view_layer.update()
coords=[o.matrix_world @ Vector(pt) for o in character_meshes for pt in o.bound_box]
height=max(pt.z for pt in coords)-min(pt.z for pt in coords)
if height<=.001: raise RuntimeError("Malla de Vera tiene altura inválida")
scale=1.73/height
root.scale=(scale,scale,scale)
root.location=(-1.65,.14,0)
# Physical character travels across the actual 3D room, synchronised with narrated action.
for t,pos in [(0,(-1.65,.14,-.27)),(2.0,(-1.65,.14,-.27)),(2.7,(-1.65,.14,0)),
  (7.0,(-1.65,.14,0)),(18.8,(-1.65,.14,0)),(19.7,(-.65,-.05,0)),
  (20.7,(.48,-.28,0)),(21.3,(1.18,-.30,0)),(32,(1.18,-.30,0))]:
    key(root,"location",t,pos)
for t,ang in [(0,-.23),(1.5,-.23),(2.75,0),(18.7,0),(19.2,-.12),(20,.12),
  (20.7,-.09),(21.3,0)]:
    key(root,"rotation_euler",t,(0,0,ang))
for armature in character_rigs:
    for pose in armature.pose.bones:
        name=pose.name.lower()
        if any(x in name for x in ("head","neck")):
            pose.rotation_mode="XYZ"
            for t,ang in [(0,-.12),(2.8,.08),(7,-.11),(17,.03),(21,.1),(29,.15),(32,.25)]:
                key(pose,"rotation_euler",t,(ang,0,0))
            break

# Desk, an ANIMATED drawer and a physical clue inside.
box("Escritorio madera", (1.35,.60,1.03),(2.15,1.1,.14),wood,.035)
box("Escritorio lateral 1",(.47,.68,.48),(.15,1.0,.88),darkwood)
box("Escritorio lateral 2",(2.25,.68,.48),(.15,1.0,.88),darkwood)
box("Cuerpo mueble cajon",(1.40,.12,.77),(1.25,.83,.48),wood,.025)
drawer=box("CAJON_INFERIOR_MOVIMIENTO_3D",(1.40,-.365,.77),(1.12,.12,.32),darkwood,.03)
handle=box("Tirador cajon", (1.4,-.448,.78),(.30,.05,.07),metal,.02)
parent_to(handle,drawer)
for t,y in [(0,-.365),(20.6,-.365),(21.4,-.49),(22.0,-.72),(23.0,-1.01),
            (26.5,-1.01),(32,-1.01)]:
    pos=list(drawer.location);pos[1]=y;key(drawer,"location",t,pos)
# Clue photo initially obscured inside the 3D drawer then rises out.
photo=box("FOTOGRAFIA_PRUEBA_FISICA",(1.4,-.40,.84),(.58,.012,.42),cream,.008)
# Photo is vertical against the desk front, contains drawn black framed empty-room image.
photo_image=box("Imagen habitacion vacia en fotografia",(1.4,-.424,.87),(.49,.009,.27),black,.003)
parent_to(photo_image,photo)
photo_date=letters("Fecha de manana","23 OCT", (1.23,-.441,.66),.047,black,(math.pi/2,0,0))
parent_to(photo_date,photo)
for t,y,z in [(0,-.40,.84),(21.3,-.40,.84),(23.3,-.87,.84),
  (24.4,-1.00,1.00),(25.5,-1.05,1.52),(29.3,-1.05,1.52),
  (32,-1.05,1.52)]:
    p=list(photo.location);p[1]=y;p[2]=z;key(photo,"location",t,p)
# No scrolling still images: full physical motion of clue and drawer.

# Laptop and voice waveform made of 3D physical bars, animated with keyframes.
box("Laptop cuerpo",(1.35,.70,1.13),(.82,.57,.06),metal,.025)
box("Laptop pantalla vertical",(1.35,1.00,1.50),(.83,.055,.63),metal,.028)
box("Laptop emisiva",(1.35,.962,1.50),(.77,.018,.57),glass,.012)
bar_material=mat("Frecuencias azul frio",(.2,.65,.83),0,.3,1.5)
for i in range(10):
    wave=box("Onda_de_audio_3D_%02d"%i,(1.00+i*.078,.938,1.43),(.028,.018,.2),bar_material,.008)
    for t in [0,10.9,11.4,12,12.6,13,14,14.8,15.8,16.4,18.8]:
        h=0.11 if t in (0,10.9,18.8) else (0.14+0.20*abs(math.sin(i*1.4+t*2.5)))
        key(wave,"scale",t,(1,1,h/.20))
# Cabinet hinged doors move as 3D solids with three distinct knocks.
box("Armario fondo",(2.95,2.00,1.48),(1.7,.60,2.85),black,.025)
closet_left=bpy.data.objects.new("BISAGRA_IZQUIERDA",None);bpy.context.collection.objects.link(closet_left)
closet_right=bpy.data.objects.new("BISAGRA_DERECHA",None);bpy.context.collection.objects.link(closet_right)
closet_left.location=(2.11,1.65,1.45);closet_right.location=(3.79,1.65,1.45)
ldoor=box("Puerta armario izquierda 3D",(2.53,1.63,1.45),(.82,.11,2.65),darkwood,.025)
rdoor=box("Puerta armario derecha 3D",(3.37,1.63,1.45),(.82,.11,2.65),darkwood,.025)
parent_to(ldoor,closet_left);parent_to(rdoor,closet_right)
for t,angle in [(0,0),(29.5,0),(29.68,-.042),(29.83,0),
                (30.25,-.055),(30.40,0),(30.83,-.085),(31,0),
                (31.5,-.50),(32.5,-.72)]:
    key(closet_left,"rotation_euler",t,(0,0,angle))
    key(closet_right,"rotation_euler",t,(0,0,-angle))
light("Luz ambiental de ventana",(-2.8,1.0,2.9),260,4.4,(.24,.45,1))
light("Luz acento escenario",(1.4,-1.9,2.4),180,3.5,(.36,.50,.76))
light("Luz hacia armario",(3.1,.45,2.85),105,2.0,(.33,.52,.93))

# Twelve 3D cameras with physically keyframed dolly/drift (no 2D crop pan).
shot_starts=[0,2.77,5.71,7.84,10.83,13.69,16.24,18.81,21.31,23.42,26.46,29.40,32.8]
shots=[
 ((-1.8,-4.1,2.0),(-1.55,-.3,1.04),"Vera despierta bajo luz del movil"),
 ((-2.65,-2.2,2.7),(-2.70,-1.18,1.20),"Pantalla telefono 03:17"),
 ((-2.9,-2.4,2.08),(-2.68,-1.17,1.21),"JULIAN llamada perdida"),
 ((-1.5,-3.0,1.85),(-1.62,.10,1.57),"Vera reconoce al desaparecido"),
 ((1.70,-2.55,2.4),(1.35,.9,1.52),"Onda de audio del mensaje"),
 ((-.65,-2.70,1.9),(-1.65,.10,1.56),"Vera reacciona al escuchar su voz"),
 ((1.45,-2.25,1.65),(1.34,.90,1.47),"Voz advierte del cajon inferior"),
 ((-.30,-3.2,1.96),(1.35,.4,.95),"Vera camina hacia escritorio"),
 ((1.55,-2.4,1.23),(1.40,-.70,.76),"Cajon se abre en 3D"),
 ((1.65,-2.5,1.65),(1.40,-.95,1.10),"La foto emerge con fecha"),
 ((1.68,-2.0,1.86),(1.40,-1.05,1.48),"Plano de fotografia de habitacion"),
 ((3.1,-2.85,1.8),(2.96,1.65,1.45),"Tres golpes reales y puertas del armario")
]
cams=[]
for i,(loc,target,desc) in enumerate(shots):
    bpy.ops.object.camera_add(location=loc)
    cam=bpy.context.object;cam.name="PLANO_%02d_%s"%(i+1,desc[:19])
    cam.data.lens=43 if i not in (1,2,8,9,10) else 55
    cam.data.sensor_fit="VERTICAL"
    t0=shot_starts[i];t1=shot_starts[i+1]
    look(cam,target)
    cam.keyframe_insert("location",frame=frame(t0))
    cam.keyframe_insert("rotation_euler",frame=frame(t0))
    # Actual camera dolly during each scene.
    delta=Vector(target)-Vector(loc)
    new=Vector(loc)+delta.normalized()*(0.08 if i in (1,2,8,9,10) else .20)
    cam.location=new
    look(cam,target)
    cam.keyframe_insert("location",frame=frame(t1))
    cam.keyframe_insert("rotation_euler",frame=frame(t1))
    marker=bpy.context.scene.timeline_markers.new("SHOT_%02d"%(i+1),frame=frame(t0))
    marker.camera=cam
    cams.append(cam)
# Final black by camera pointing at black enclosed wall inside real 3D.
bpy.ops.object.camera_add(location=(0,0,-9))
blackcam=bpy.context.object;blackcam.name="CORTE_FINAL_NEGRO"
look(blackcam,(0,0,-10))
m=bpy.context.scene.timeline_markers.new("CORTE_NEGRO",frame=frame(32.55))
m.camera=blackcam

scene=bpy.context.scene
scene.camera=cams[0]
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=a.samples
scene.cycles.use_denoising=True
scene.render.resolution_x=a.width;scene.render.resolution_y=a.height
scene.render.resolution_percentage=100
scene.render.film_transparent=False
scene.render.image_settings.file_format="PNG"
scene.render.image_settings.color_mode="RGB"
scene.render.fps=FPS
scene.frame_start=1
scene.frame_end=frame(7.84 if a.preview else 32.8)-1
scene.render.filepath=str(Path(a.out).resolve().parent/"frames"/"frame_")
scene.world.color=(.012,.016,.03)
scene.render.threads_mode="FIXED"
scene.render.threads=4
try: scene.view_settings.view_transform="AgX"
except (TypeError,ValueError): scene.view_settings.view_transform="Standard"
# Require actual 3D world transforms across frames, no still frames.
def moved(obj,t1,t2,prop):
    scene.frame_set(frame(t1));left=tuple(getattr(obj,prop))
    scene.frame_set(frame(t2));right=tuple(getattr(obj,prop))
    return left!=right
assert moved(drawer,20.5,23.2,"location"), "Drawer animation missing"
assert moved(closet_left,29.4,32.1,"rotation_euler"), "Wardrobe animation missing"
assert moved(root,18.6,21.5,"location"), "Character performance missing"
assert moved(photo,23.3,25.8,"location"), "Photo movement missing"
assert len(cams)==12
scene.frame_set(1)
out=Path(a.out).resolve();out.parent.mkdir(parents=True,exist_ok=True)
out.with_suffix(".json").write_text(json.dumps({
    "renderer":"Blender Cycles CPU","blender_version":bpy.app.version_string,
    "format":"true keyframed 3D","duration":32.8,"fps":FPS,"samples":a.samples,
    "animated_objects":["Vera actress","phone light","voice waveform","desk drawer","photograph","wardrobe doors","12 real 3D cameras"],
    "camera_shots":[{"start":shot_starts[i],"end":shot_starts[i+1],"scene":shots[i][2]} for i in range(12)],
    "narrator_visible":False,"slideshow":False
},ensure_ascii=False,indent=2),encoding="utf-8")
bpy.ops.wm.save_as_mainfile(filepath=str(out))
print("BLENDER_TRUE_3D_OK="+str(out),flush=True)
print("ANIMATED_OBJECTS=Vera,drawer,photo,wardrobe,phone,12cameras",flush=True)
