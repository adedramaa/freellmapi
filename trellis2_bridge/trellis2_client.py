#!/usr/bin/env python3
"""Agencia 3D / cliente de Microsoft TRELLIS.2 por Gradio.
--mode probe: solo metadatos (GPU 0)
--mode generate: una sola generacion y una exportacion ZeroGPU gratuita.
Generación autenticada exclusivamente mediante HF_TOKEN de GitHub Environment.
No usa tarjetas, proveedores de pago ni reintentos automáticos.
"""
from __future__ import annotations
import argparse
import json
import os
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
    if isinstance(result,(str,Path)):
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

def require_token():
    """Falla ANTES de cualquier subida o GPU si no existe autenticación."""
    token=os.getenv('HF_TOKEN','').strip()
    if not token or not token.startswith('hf_'):
        raise RuntimeError('AUTH_REQUIRED: falta HF_TOKEN; prohibido generar como anonimo')
    return token

def verify_account(token):
    """Validación sin GPU ni impresión del token (no lo registra en logs)."""
    from huggingface_hub import HfApi
    who=HfApi().whoami(token=token)
    name=who.get('name')
    if not name:
        raise RuntimeError('AUTH_INVALID: Hugging Face no devolvio usuario')
    if name!='adedrama':
        raise RuntimeError('AUTH_MISMATCH: cuenta de Hugging Face diferente')
    # Cuentas PRO o de pago pueden consumir creditos al exceder cuota;
    # se bloquean por la regla absoluta de coste cero.
    if who.get('isPro') or who.get('is_pro'):
        raise RuntimeError('PAID_ACCOUNT_BLOCKED: requerimos cuenta free')
    return {'status':'AUTH_OK','account':name,'gpu_calls':0}

def generate(src:Path, out_dir:Path, token:str):
    if not src.is_file() or src.suffix.lower() not in ('.png','.jpg','.jpeg'):
        raise ValueError('El archivo local debe ser PNG/JPG')
    if src.stat().st_size>8*1024*1024:
        raise ValueError('Imagen mayor de 8 MB')
    from gradio_client import Client, handle_file
    client=Client(SPACE,token=token,verbose=False,analytics_enabled=False)  # Cuota de cuenta FREE; no se usan proveedores de pago.
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
    p.add_argument('--mode',choices=['probe','auth-check','generate'],default='probe')
    p.add_argument('--image',type=Path)
    p.add_argument('--out',type=Path,default=Path('output'))
    p.add_argument('--accept-free-quota',action='store_true')
    a=p.parse_args()
    if a.mode=='probe':
        print(json.dumps(probe(),ensure_ascii=False))
        return
    try:
        token=require_token()
        account=verify_account(token)
        print(json.dumps(account,ensure_ascii=False))
    except Exception as e:
        print('AUTH_PREFLIGHT_FAILED: '+type(e).__name__,file=sys.stderr)
        raise SystemExit(2)
    if a.mode=='auth-check':
        return
    # Verificar endpoints antes de consumir tiempo de GPU.
    print(json.dumps(probe(),ensure_ascii=False))
    if not a.accept_free_quota or a.image is None:
        raise SystemExit('Para generar se necesita --image y --accept-free-quota')
    try:
        glb=generate(a.image,a.out,token)
    except Exception as e:
        # No emitir tokens, URLs firmadas, trazas HTTP o credenciales a GitHub publico.
        message=str(e).lower()
        if 'quota' in message or 'zerogpu' in message:
            print('TRELLIS2_LIMIT: cuota gratuita insuficiente o no disponible',file=sys.stderr)
        else:
            print('TRELLIS2_FAILED: '+type(e).__name__,file=sys.stderr)
        raise SystemExit(1)
    print('TRELLIS2_GLB_OK',glb,glb.stat().st_size)
if __name__=='__main__':
    main()
