#!/usr/bin/env python3
"""Agencia 3D / cliente de Microsoft TRELLIS.2 por Gradio.
--mode probe: solo metadatos (GPU 0)
--mode generate: una sola generacion y una exportacion ZeroGPU gratuita.
NO utiliza tokens, tarjeta, API de pago ni reintentos.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import sys
from urllib.request import urlopen

SPACE = 'microsoft/TRELLIS.2'
INFO_URL = 'https://microsoft-trellis-2.hf.space/gradio_api/info'
ENDPOINTS = ('/preprocess_image', '/image_to_3d', '/extract_glb')
# Parámetros comprobados contra la interfaz oficial (1024 -> 512 para ahorrar GPU).
DEFAULT_PARAMS = (0,'512',7.5,0.7,12,5.0,7.5,0.5,12,3.0,1.0,0.0,12,3.0)

def probe():
    with urlopen(INFO_URL, timeout=15) as resp:
        data=json.load(resp)
    named=data.get('named_endpoints') or {}
    missing=[ep for ep in ENDPOINTS if ep not in named]
    if missing:
        raise RuntimeError('API ha cambiado; faltan '+str(missing))
    n=len(named['/image_to_3d'].get('parameters') or [])
    e=len(named['/extract_glb'].get('parameters') or [])
    if (n,e)!=(15,2):
        raise RuntimeError('API alterada: generacion '+str(n)+' args, extraccion '+str(e))
    return {'status':'API_OK','space':SPACE,'endpoints':list(ENDPOINTS),
            'inputs_generate':n,'inputs_extract':e,'gpu_calls':0}

def local_path(result):
    if isinstance(result,str):
        f=Path(result)
        return f if f.is_file() else None
    if isinstance(result,dict):
        for k in ('path','name'):
            if result.get(k) and Path(result[k]).is_file():
                return Path(result[k])
    if isinstance(result,(list,tuple)):
        for item in result:
            p=local_path(item)
            if p:
                return p
    return None

def generate(src:Path, out_dir:Path):
    if not src.is_file() or src.suffix.lower() not in ('.png','.jpg','.jpeg'):
        raise ValueError('El archivo local debe ser PNG/JPG')
    if src.stat().st_size>8*1024*1024:
        raise ValueError('Imagen mayor de 8 MB')
    from gradio_client import Client, handle_file
    client=Client(SPACE,verbose=False)  # Anónimo: sin token, crédito ni cargos
    prep=client.predict(handle_file(str(src)),api_name='/preprocess_image')
    prep_path=local_path(prep)
    if prep_path is None:
        raise RuntimeError('La preparación no entregó archivo')
    client.predict(handle_file(str(prep_path)),*DEFAULT_PARAMS,api_name='/image_to_3d')
    # Gradio Client conserva automáticamente el estado por sesión.
    extracted=client.predict(300000,1024,api_name='/extract_glb')
    glb=local_path(extracted)
    if glb is None or glb.stat().st_size<=100:
        raise RuntimeError('El servidor no entregó GLB')
    out_dir.mkdir(parents=True,exist_ok=True)
    dest=out_dir/'trellis2_resultado.glb'
    shutil.copyfile(glb,dest)
    with dest.open('rb') as f:
        if f.read(4)!=b'glTF':
            raise RuntimeError('La descarga no es GLB válido')
    return dest

def main():
    p=argparse.ArgumentParser(description='Agencia3D TRELLIS.2 ZeroGPU: gratis y sin PC')
    p.add_argument('--mode',choices=['probe','generate'],default='probe')
    p.add_argument('--image',type=Path)
    p.add_argument('--out',type=Path,default=Path('output'))
    p.add_argument('--accept-free-quota',action='store_true')
    a=p.parse_args()
    print(json.dumps(probe(),ensure_ascii=False))
    if a.mode=='probe':
        return
    if not a.accept_free_quota or a.image is None:
        raise SystemExit('Para generar se necesita --image y --accept-free-quota')
    try:
        glb=generate(a.image,a.out)
    except Exception as e:
        print('TRELLIS2_NO_COMPLETADO: '+type(e).__name__+': '+str(e)[:400],file=sys.stderr)
        raise SystemExit(1)
    print('TRELLIS2_GLB_OK',glb,glb.stat().st_size)
if __name__=='__main__':
    main()
