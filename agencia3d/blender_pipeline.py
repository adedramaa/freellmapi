"""Agencia 3D: procesamiento real con Blender sin GUI.
Ejecutar: blender -b --factory-startup --python agencia3d/blender_pipeline.py -- --out output
Opcional: --input modelo.glb (la entrada permanece intacta).
Solo software libre; sin redes, credenciales ni APIs de pago.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector

def args():
    p = argparse.ArgumentParser()
    p.add_argument('--out', default='output')
    p.add_argument('--input', default='')
    return p.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])

def reset():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def material(name, rgb):
    m = bpy.data.materials.new(name=name)
    m.diffuse_color = (*rgb, 1.0)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (*rgb, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.72
    return m

def make_fixture():
    """Prueba de funciones: geometría de verdad (no el personaje final)."""
    sand = material('ARENA_A3D', (.89, .64, .37))
    ink = material('BORDE_A3D', (.10, .19, .17))
    green = material('VERDE_A3D', (.22, .53, .34))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 2.5))
    plate = bpy.context.object
    plate.name = '01_PLACA_80x65x5mm'
    plate.dimensions = (80, 65, 5)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    plate.data.materials.append(sand)
    bevel = plate.modifiers.new('Bordes_reales', 'BEVEL')
    bevel.width = 3.2
    bevel.segments = 7
    bpy.context.view_layer.objects.active = plate
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1, location=(-13, 0, 17))
    dome = bpy.context.object
    dome.name = '02_BULTO_VOLUMETRICO_3D'
    dome.scale = (19, 17, 13)
    dome.data.materials.append(green)
    bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_torus_add(major_segments=80, minor_segments=16, location=(15, 2, 8), major_radius=12, minor_radius=2.4)
    ring = bpy.context.object
    ring.name = '03_ANILLO_EN_3D'
    ring.data.materials.append(ink)
    bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0, radius2=8, depth=3, location=(0, 22, 8))
    marker = bpy.context.object
    marker.name = '04_MARCADOR_DE_ORIENTACION'
    marker.rotation_euler[2] = math.pi / 4
    marker.data.materials.append(ink)

def import_glb(path):
    src = Path(path)
    if not src.is_file() or src.suffix.lower() not in {'.glb', '.gltf'}:
        raise ValueError('Entrada permitida: archivo GLB/GLTF existente')
    bpy.ops.import_scene.gltf(filepath=str(src.absolute()))
    if not any(o.type == 'MESH' for o in bpy.context.scene.objects):
        raise RuntimeError('El GLB no contiene mallas')

def set_camera(location, target):
    cam = bpy.data.objects.get('CAMARA_RENDER')
    if cam is None:
        camdata = bpy.data.cameras.new('CAMARA_A3D')
        cam = bpy.data.objects.new('CAMARA_RENDER', camdata)
        bpy.context.collection.objects.link(cam)
    cam.location = location
    direction = Vector(target) - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 113
    bpy.context.scene.camera = cam

def render(path):
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'MATERIAL'
    scene.display.shading.show_shadows = True
    scene.render.resolution_x = 640
    scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)

def filehash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    a = args()
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    reset()
    if a.input:
        import_glb(a.input)
        source = 'archivo_importado'
    else:
        make_fixture()
        source = 'calibracion_geometrica'
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    assert meshes, 'No se creó geometría'
    set_camera((0, -140, 116), (0, 0, 6))
    render(out / 'vista_frente.png')
    set_camera((130, -140, 115), (0, 0, 6))
    render(out / 'vista_tres_cuartos.png')
    bpy.ops.wm.save_as_mainfile(filepath=str(out / 'modelo.blend'))
    bpy.ops.object.select_all(action='DESELECT')
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.gltf(filepath=str(out / 'modelo.glb'), export_format='GLB', use_selection=True)
    if hasattr(bpy.ops.wm, 'stl_export'):
        bpy.ops.wm.stl_export(filepath=str(out / 'modelo.stl'), export_selected_objects=True)
    else:
        bpy.ops.export_mesh.stl(filepath=str(out / 'modelo.stl'), use_selection=True)
    manifest = {
        'source': source,
        'blender_version': bpy.app.version_string,
        'mesh_count': len(meshes),
        'objects': [o.name for o in meshes],
        'units': 'fixture coordinates are millimeters; GLB/STL follow Blender scene units',
        'files_sha256': {f: filehash(out / f) for f in ['modelo.blend', 'modelo.glb', 'modelo.stl', 'vista_frente.png', 'vista_tres_cuartos.png']},
        'note': 'Prueba de Blender real, NO es reconstruccion del perro ni TRELLIS.2.'
    }
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    for name in manifest['files_sha256']:
        if (out / name).stat().st_size < 512:
            raise RuntimeError('Exportación vacía: ' + name)
    print('AGENCIA3D_OK ' + json.dumps({'blender': manifest['blender_version'], 'meshes': len(meshes), 'outputs': list(manifest['files_sha256'])}))

if __name__ == '__main__':
    main()
