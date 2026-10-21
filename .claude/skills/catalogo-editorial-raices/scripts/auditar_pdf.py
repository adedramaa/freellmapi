#!/usr/bin/env python3
"""Revisión auxiliar: PDF, recuento SKU/texto y miniaturas. No sustituye revisión visual humana."""
import argparse
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pdf')
    ap.add_argument('--out', default='auditoria-paginas')
    ap.add_argument('--catalogo', default=None)
    args = ap.parse_args()
    try:
        import fitz
    except ImportError:
        raise SystemExit('Requiere la biblioteca gratuita PyMuPDF (pip install pymupdf).')
    target = Path(args.pdf).resolve()
    if not target.is_file():
        raise SystemExit(f'PDF no encontrado: {target}')
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(target)
    if not len(doc):
        raise SystemExit('ERROR: PDF sin páginas')
    txt = ''
    vacias = []
    for i, page in enumerate(doc):
        txt += page.get_text() + '\n'
        if not page.get_text().strip():
            vacias.append(i+1)
        pix = page.get_pixmap(matrix=fitz.Matrix(0.85, 0.85), alpha=False)
        pix.save(str(out / f'pagina-{i+1:03d}.png'))
    errors = []
    if vacias:
        errors.append('Páginas sin texto extraíble (revisar): ' + ', '.join(map(str, vacias)))
    if args.catalogo:
        from validar_catalogo import validar
        data, fallas, _ = validar(args.catalogo)
        errors.extend(fallas)
        if data and not fallas:
            for item in data['productos']:
                if str(item['sku']).casefold() not in txt.casefold():
                    errors.append(f'No aparece SKU en texto PDF: {item["sku"]}')
    print('Páginas PDF:', len(doc))
    print('Miniaturas para revisar:', out)
    if errors:
        for e in errors: print('REVISAR:', e)
        return 2
    print('Chequeos automáticos básicos OK. Todavía es OBLIGATORIO inspeccionar visualmente todas las imágenes generadas.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
