#!/usr/bin/env python3
"""HTML A4 básico de catálogo: solo desde inventario JSON verificado."""
import argparse
from collections import OrderedDict
from decimal import Decimal
from html import escape
from pathlib import Path
from urllib.parse import urlparse
from validar_catalogo import validar


def texto(value):
    return escape(str(value), quote=True)


def precio_format(valor, moneda):
    n = Decimal(str(valor))
    txt = f'{n:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    if txt.endswith(',00'):
        txt = txt[:-3]
    return f'{moneda} {txt}'


def card(p, base, moneda):
    image = Path(p['imagen'])
    if not image.is_absolute():
        image = (base / image).resolve()
    img_url = image.as_uri()
    nombre, codigo = texto(p['nombre']), texto(p['sku'])
    desc = f'<p class="card-description">{texto(p["descripcion"])}</p>' if p.get('descripcion') else ''
    return f'''<article class="card">
       <div class="photo"><img src="{texto(img_url)}" alt="Fotografía oficial de {nombre}"></div>
       <div class="product-meta"><div class="sku">REF. {codigo}</div><h3>{nombre}</h3>{desc}</div>
       <div class="price">{texto(precio_format(p['precio'], moneda))}</div>
     </article>'''


def page(body, number, title, company, footer):
    return f'''<section class="page">
     <div class="page-top"><span class="page-company">{texto(company)}</span><span>{texto(title)}</span></div>
     {body}
     <div class="page-bottom"><span>{texto(footer)}</span><span>{number:02d}</span></div>
    </section>'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('catalogo')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    data, errors, warnings = validar(args.catalogo)
    if errors:
        raise SystemExit('No puede generarse el catálogo con errores de validación:\n- ' + '\n- '.join(errors))
    cat_path = Path(args.catalogo).resolve()
    output_path = Path(args.out).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    css_path = Path(__file__).resolve().parent.parent / 'assets' / 'catalogo.css'
    css = css_path.read_text(encoding='utf-8')
    company, title = data['empresa'], data['titulo']
    footer = f'Edición {data["fecha_corte"]}'
    cover = f'''<section class="page cover">
        <div class="cover-head"><span>CATÁLOGO · EDICIÓN {texto(data['fecha_corte'])}</span><span>VENTAS MAYORISTAS</span></div>
        <div class="cover-main"><div class="cover-rule"></div><p class="cover-kicker">SELECCIÓN DE PRODUCTOS</p>
        <h1>{texto(company)}</h1><h2>{texto(title)}</h2>
        <p class="cover-desc">Información comercial organizada por familias.<br>Imágenes de productos asociadas a sus referencias.</p></div>
        <div class="cover-footer"><span>{len(data['productos'])} REFERENCIAS</span><span>{texto(data['moneda'])}</span></div>
     </section>'''
    categories = OrderedDict()
    for p in data['productos']:
        categories.setdefault(p['categoria'], []).append(p)
    pages, num = [cover], 2
    for cat, products in categories.items():
        for i in range(0, len(products), 4):
            bloque = products[i:i+4]
            counter = f'{i+1:02d}–{i+len(bloque):02d} / {len(products):02d}'
            heading = f'''<div class="section-heading"><div><p class="eyebrow">FAMILIA DE PRODUCTOS</p><h2>{texto(cat)}</h2></div><span>{counter}</span></div>'''
            cards = '<div class="card-grid">' + ''.join(card(p, cat_path.parent, data['moneda']) for p in bloque) + '</div>'
            pages.append(page(heading + cards, num, title, company, footer))
            num += 1
    web = (data.get('contacto') or {}).get('web', '')
    if web and urlparse(web).scheme not in ('http', 'https'):
        web = ''
    contact = (f'<p class="contact-url">{texto(web)}</p>' if web else '<p>Consulta los canales oficiales de la empresa para comprar.</p>')
    pages.append(f'''<section class="page end-page"><div class="page-top">{texto(company)} · {texto(title)}</div>
    <div class="end-main"><p class="eyebrow">CONTACTO</p><h2>¿Hacemos tu próximo pedido?</h2>{contact}
    <p class="end-note">Verifica vigencia de precios y disponibilidad con el vendedor antes de confirmar.</p></div>
    <div class="page-bottom"><span>Edición {texto(data['fecha_corte'])}</span><span>{num:02d}</span></div></section>''')
    html = '<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + texto(title) + '</title><style>' + css + '</style></head><body>' + '\n'.join(pages) + '</body></html>'
    output_path.write_text(html, encoding='utf-8')
    print(f'HTML: {output_path} | Productos: {len(data["productos"])} | Páginas previstas: {len(pages)}')
    print('Paso pendiente: exportar PDF y revisar visualmente TODAS las páginas; el HTML NO equivale a aprobación.')

if __name__ == '__main__':
    main()
