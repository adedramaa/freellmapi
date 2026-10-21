#!/usr/bin/env python3
"""Bloquea catálogos con datos sin verificar. Usa únicamente stdlib."""
import argparse
import json
import sys
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse

ALLOWED_EXT = {'.jpg', '.jpeg', '.png', '.webp', '.tif', '.tiff'}

def validar(ruta):
    errores, avisos = [], []
    ruta = Path(ruta).resolve()
    try:
        data = json.loads(ruta.read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        return None, [f'JSON inaccesible o inválido: {e}'], []
    if not isinstance(data, dict):
        return None, ['La raíz debe ser un objeto JSON.'], []
    for campo in ('empresa', 'titulo', 'moneda', 'fecha_corte'):
        if not isinstance(data.get(campo), str) or not data[campo].strip():
            errores.append(f'Falta {campo} válido')
    if not isinstance(data.get('fuentes'), list) or not data['fuentes'] or not all(isinstance(x, str) and x.strip() for x in data['fuentes']):
        errores.append('fuentes debe contener al menos una referencia oficial no vacía')
    productos = data.get('productos')
    if not isinstance(productos, list) or not productos:
        errores.append('productos debe ser una lista no vacía')
        return data, errores, avisos
    codigos = []
    for i, p in enumerate(productos, 1):
        prefijo = f'Producto #{i}'
        if not isinstance(p, dict):
            errores.append(prefijo + ': se esperaba objeto')
            continue
        for campo in ('sku', 'nombre', 'categoria', 'fuente_precio', 'imagen', 'fuente_imagen'):
            if not isinstance(p.get(campo), str) or not p[campo].strip():
                errores.append(f'{prefijo}: {campo} faltante')
        sku = p.get('sku')
        if isinstance(sku, str) and sku.strip():
            codigos.append(sku.strip().casefold())
        if p.get('verificado') is not True:
            errores.append(f'{prefijo}: verificado no es true; falta validación documental')
        precio = p.get('precio')
        if isinstance(precio, bool) or precio is None:
            errores.append(f'{prefijo}: precio no es un número válido')
        else:
            try:
                if Decimal(str(precio)) <= 0 or not Decimal(str(precio)).is_finite():
                    errores.append(f'{prefijo}: precio debe ser positivo y finito')
            except (InvalidOperation, TypeError):
                errores.append(f'{prefijo}: precio inválido')
        foto = p.get('imagen', '')
        if isinstance(foto, str) and foto.strip():
            if urlparse(foto).scheme in ('http', 'https'):
                errores.append(f'{prefijo}: imagen remota debe descargarse y asociarse a fuente oficial antes de exportar')
            else:
                imagepath = Path(foto)
                if not imagepath.is_absolute():
                    imagepath = ruta.parent / imagepath
                if not imagepath.is_file():
                    errores.append(f'{prefijo}: no existe imagen local {imagepath}')
                elif imagepath.suffix.lower() not in ALLOWED_EXT:
                    errores.append(f'{prefijo}: formato no soportado para imagen {imagepath.suffix}')
                elif imagepath.stat().st_size < 2048:
                    avisos.append(f'{prefijo}: imagen de menos de 2 KB, comprobar calidad')
    for sku, cuenta in Counter(codigos).items():
        if cuenta > 1:
            errores.append(f'SKU duplicado: {sku} ({cuenta} entradas)')
    return data, errores, avisos

def main():
    parser = argparse.ArgumentParser(description='Valida datos originales para un catálogo comercial.')
    parser.add_argument('catalogo', help='Ruta al catalogo.json autorizado')
    args = parser.parse_args()
    data, errores, avisos = validar(args.catalogo)
    cantidad = len(data.get('productos', [])) if data else 0
    print(f'Productos revisados: {cantidad}')
    for a in avisos:
        print('AVISO:', a)
    if errores:
        for e in errores:
            print('BLOQUEANTE:', e)
        print(f'BLOQUEADO: {len(errores)} problema(s); PDF NO publicable.')
        return 2
    print('Validación estructural aprobada; todavía se requiere comprobación visual y documental de fuentes reales.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
