#!/usr/bin/env python3
"""Editorial PDF Raices: public product photos and real SKU, zero prices.
This is an isolated candidate generator; never deploys to the commercial panel.
"""
from __future__ import annotations
import json, math, os, re, time, html
from io import BytesIO
from pathlib import Path
import requests
from PIL import Image, ImageOps, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
import fitz

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'
OUT.mkdir(exist_ok=True)
PHOTOS=OUT/'photos'
PHOTOS.mkdir(exist_ok=True)
API='https://raicesregalos.com/wp-json/wc/store/v1/products'
SESSION=requests.Session()
SESSION.headers.update({'User-Agent':'Raices-Editorial-20P/1.0 (public-catalogue)','Accept':'application/json'})
W,H=A4
def rgbhex(v):return HexColor(v)
THEME=json.loads((ROOT/'theme.json').read_text(encoding='utf8'))
INK=rgbhex(THEME['ink']); PAPER=rgbhex(THEME['paper']); FOREST=rgbhex(THEME['forest'])
COPPER=rgbhex(THEME['copper']); MUTED=rgbhex(THEME['muted']); CREAM=rgbhex(THEME['cream'])
for tag,path in [('Sans','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),('Bold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),('Serif','/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf')]:
    pdfmetrics.registerFont(TTFont(tag,path))
def clean(v):
    return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>','',str(v or '')))).strip()
def load_products():
    products=[]
    for page in range(1,10):
        try:
            r=SESSION.get(API,params={'per_page':100,'page':page,'catalog_visibility':'visible','orderby':'id','order':'desc'},timeout=35)
            if not r.ok:
                print('fetch',page,r.status_code)
                break
            items=r.json()
            if not isinstance(items,list) or not items:break
            products.extend(items)
            print('Product page:',page,'added',len(items),'total',len(products),flush=True)
            if len(items)<100:break
        except Exception as e: print('product_error',page,str(e)[:180]);break
    if len(products)<70:raise RuntimeError('Insufficient real store products: '+str(len(products)))
    rows=[];seen=set()
    for p in products:
        sku=clean(p.get('sku')).upper()
        image=(p.get('images') or [{}])[0].get('src') or ''
        if not sku or not image or sku in seen:continue
        cats=' '.join(clean(z.get('name')) for z in p.get('categories',[])).lower()
        title=clean(p.get('name'))
        if not title:continue
        if len(sku)>30:continue
        seen.add(sku)
        mix=(title+' '+cats).lower()
        group=('cuero' if any(k in mix for k in ('billeter','cuero','matera','mochila','bolso','morral')) else
               'asado' if any(k in mix for k in ('asado','tabla','cuchillo','picada','parrilla','set asad','cubierto','destapador')) else
               'mate' if any(k in mix for k in ('mate','termo','bombilla','yerbera','matero')) else 'regalos')
        score=sum(2 for word in ('negro','negra','marrón','marron','cuero','madera','oscuro','acero','premium','clásico','clasico') if word in mix)
        rows.append(dict(sku=sku,name=title[:83],image=image,source_id=p.get('id'),categories=cats,group=group,score=score))
    rows.sort(key=lambda x:(-x['score'],x['sku']))
    return rows

def fetch_photo(p):
    target=PHOTOS/(re.sub('[^A-Za-z0-9_-]','_',p['sku'])[:70]+'.jpg')
    if target.exists() and target.stat().st_size>3000:return target
    try:
        response=SESSION.get(p['image'],timeout=25)
        response.raise_for_status()
        if len(response.content)>15*1024*1024:return None
        im=Image.open(BytesIO(response.content))
        im.load()
        im=ImageOps.exif_transpose(im)
        if im.width<160 or im.height<160:return None
        if im.mode=='RGBA':
            background=Image.new('RGB',im.size,'#F5F2EA')
            background.paste(im,mask=im.getchannel('A'));im=background
        else:im=im.convert('RGB')
        im.thumbnail((1450,1450),Image.Resampling.LANCZOS)
        im.save(target,'JPEG',quality=83,optimize=True)
        return target
    except Exception as e:
        print('photo_error',p['sku'],str(e)[:90],flush=True)
        return None

def take(rows,group,n,taken,prefer=None):
    pool=[x for x in rows if x['group']==group and x['sku'] not in taken]
    if prefer:pool.sort(key=lambda x: (not (x['sku'].startswith(prefer) or prefer.lower() in x['name'].lower()),-x['score']))
    pool+= [x for x in rows if x['sku'] not in taken and x not in pool]
    selected=[]
    for p in pool:
        if len(selected)>=n:break
        f=fetch_photo(p)
        if f:
            p=dict(p,local=str(f));selected.append(p);taken.add(p['sku'])
    if len(selected)<n:raise RuntimeError('Could not retrieve enough verified product images.')
    return selected
def box(c,x,y,w,h,color):
    c.setFillColor(color);c.rect(x,y,w,h,stroke=0,fill=1)
def txt(c,x,y,value,size=13,font='Sans',color=INK):
    c.setFillColor(color);c.setFont(font,size);c.drawString(x,y,str(value))
def image_contain(c,path,x,y,w,h,padding=0):
    im=Image.open(path);iw,ih=im.size
    scale=min((w-2*padding)/iw,(h-2*padding)/ih)
    nw,nh=iw*scale,ih*scale
    c.drawImage(str(path),x+(w-nw)/2,y+(h-nh)/2,nw,nh,mask='auto')
def fit_lines(label,max_width,font='Bold',size=14,max_lines=2):
    words=label.split();lines=[];current=''
    for word in words:
        proposal=(current+' '+word).strip()
        if pdfmetrics.stringWidth(proposal,font,size)>max_width and current:
            lines.append(current);current=word
            if len(lines)>=max_lines:break
        else:current=proposal
    if len(lines)<max_lines and current:lines.append(current)
    if len(lines)>max_lines:lines=lines[:max_lines]
    return lines
def label(c,p,x,y,max_w,sku_size=18,name_size=11,light=False):
    col=PAPER if light else INK
    txt(c,x,y,'REF. '+p['sku'],sku_size,'Bold',col)
    for ix,line in enumerate(fit_lines(p['name'],max_w,'Sans',name_size,2)):
        txt(c,x,y-23-ix*15,line,name_size,'Sans',col)
def footer(c,n,section,light=False):
    color=PAPER if light else MUTED
    c.setStrokeColor(color);c.setLineWidth(.4);c.line(40,44,W-40,44)
    txt(c,40,29,'RAÍCES REGALOS   /   COLECCIÓN SIN PRECIOS',8,'Sans',color)
    txt(c,W-104,29,f'{n:02d} / 20',9,'Bold',color)
def common(c,n,section,bg=PAPER):
    box(c,0,0,W,H,bg);txt(c,40,H-38,'RAÍCES  /  SELECCIÓN EDITORIAL',10,'Bold',FOREST if bg==PAPER else PAPER)
    txt(c,W-126,H-38,section.upper()[:18],8,'Sans',MUTED if bg==PAPER else CREAM)
    footer(c,n,section,bg!=PAPER)
def material(c,path,x,y,w,h):
    box(c,x,y,w,h,CREAM)
    image_contain(c,path,x+6,y+6,w-12,h-12)
def drawing(c,items,n,group):
    if n==1:
        box(c,0,0,W,H,FOREST)
        box(c,350,80,W-350,690,CREAM)
        image_contain(c,items[0]['local'],350,140,W-350,550,5)
        txt(c,40,H-75,'RAÍCES',31,'Serif',PAPER)
        txt(c,40,H-137,'EDICIÓN',13,'Bold',CREAM)
        cover_words=THEME.get('cover_title','EL ARTE DE ELEGIR').split()
        if len(cover_words)>3:cover_words=[' '.join(cover_words[:2]),cover_words[2],' '.join(cover_words[3:])]
        cover_words=(cover_words+['',''])[:3]
        for i,word in enumerate(cover_words):txt(c,40,H-204-i*45,word,33,'Serif',PAPER)
        box(c,40,H-319,66,3,COPPER)
        txt(c,40,H-366,'Regalos, mate y asado',12,'Sans',CREAM)
        txt(c,40,H-386,'Una selección para elegir.',11,'Sans',CREAM)
        label(c,365,87,200,18,11,True) if False else label(c,items[0],365,96,198,16,10,False)
        footer(c,n,group,True);c.showPage();return
    if n==20:
        box(c,0,0,W,H,FOREST)
        txt(c,44,H-100,'LO QUE',41,'Serif',PAPER)
        txt(c,44,H-152,'PERMANECE',41,'Serif',PAPER)
        material(c,items[0]['local'],208,224,347,405)
        label(c,items[0],45,223,200,17,11,True)
        txt(c,44,134,'raicesregalos.com',17,'Bold',PAPER)
        txt(c,44,109,'Consulta disponibilidad con el equipo.',10,'Sans',CREAM)
        footer(c,n,group,True);c.showPage();return
    special=n in (2,10)
    if special:
        box(c,0,0,W,H,FOREST)
        txt(c,40,H-81,'EL OFICIO',39,'Serif',PAPER) if n==2 else txt(c,40,H-81,'EL ENCUENTRO',34,'Serif',PAPER)
        txt(c,40,H-120,'DE REGALAR' if n==2 else 'ALREDEDOR DEL FUEGO',17,'Sans',CREAM)
        material(c,items[0]['local'],40,315,340,310)
        material(c,items[1]['local'],399,345,156,220)
        label(c,items[0],40,292,320,17,10,True)
        label(c,items[1],399,322,155,16,9,True)
        footer(c,n,group,True);c.showPage();return
    dark=(n%6==3)
    common(c,n,group,FOREST if dark else PAPER)
    labels={'cuero':'EL DETALLE IMPORTA','mate':'EL RITUAL COTIDIANO','asado':'HECHOS PARA COMPARTIR','regalos':'UNA IDEA PARA REGALAR'}
    txt(c,40,H-95,labels.get(group,'OBJETOS ELEGIDOS'),25,'Serif',PAPER if dark else INK)
    txt(c,40,H-119,'UNA SELECCIÓN DE RAÍCES REGALOS',9,'Bold',CREAM if dark else COPPER)
    mode=n%6
    if mode==0:
        # Large left image + two smaller portraits at right.
        material(c,items[0]['local'],40,190,319,479)
        material(c,items[1]['local'],379,421,176,248)
        material(c,items[2]['local'],379,190,176,160)
        label(c,items[0],42,159,315,18,11)
        label(c,items[1],379,393,176,16,9)
        label(c,items[2],379,166,176,16,9)
    elif mode==1:
        material(c,items[0]['local'],40,364,515,308)
        material(c,items[1]['local'],40,132,217,183)
        material(c,items[2]['local'],288,132,267,183)
        label(c,items[0],42,333,510,19,11)
        label(c,items[1],42,104,211,16,9)
        label(c,items[2],290,104,265,16,9)
    elif mode==2:
        material(c,items[0]['local'],40,224,250,449)
        material(c,items[1]['local'],315,366,240,307)
        material(c,items[2]['local'],315,225,240,110)
        label(c,items[0],42,194,247,18,11)
        label(c,items[1],315,337,237,16,9)
        label(c,items[2],315,196,238,16,9)
    elif mode==3:
        # Full dark editorial with offset images, asymmetrical composition.
        material(c,items[0]['local'],205,225,350,448)
        material(c,items[1]['local'],40,451,138,221)
        material(c,items[2]['local'],40,245,138,153)
        label(c,items[0],205,194,345,19,11,True)
        label(c,items[1],40,424,152,16,9,True)
        label(c,items[2],40,220,152,16,9,True)
    elif mode==4:
        # Paired oversized product imagery and a lower editorial strip.
        material(c,items[0]['local'],40,368,340,305)
        material(c,items[1]['local'],400,368,155,305)
        material(c,items[2]['local'],170,127,385,170)
        label(c,items[0],40,340,334,20,12)
        label(c,items[1],400,342,153,16,9)
        label(c,items[2],170,101,383,17,10)
    else:
        # Panoramic image + two bottom details; distinct from rigid grids.
        material(c,items[0]['local'],40,263,515,410)
        material(c,items[1]['local'],40,113,226,120)
        material(c,items[2]['local'],291,113,264,120)
        label(c,items[0],40,240,508,19,11)
        label(c,items[1],40,93,221,16,9)
        label(c,items[2],291,93,258,16,9)
    c.showPage()

def main():
    products=load_products()
    taken=set()
    PDF=OUT/'RAICES_SELECCION_EDITORIAL_20P_SIN_PRECIOS.pdf'
    pages=[]
    for pageno in range(1,21):
        if pageno==1:group='regalos';items=take(products,'cuero',1,taken)
        elif pageno==2:group='regalos';items=take(products,'cuero',2,taken)
        elif 3<=pageno<=5:group='cuero';items=take(products,'cuero',3,taken)
        elif 6<=pageno<=9:
            group='mate'
            prefix={6:'MAT',7:'TER',8:'SET',9:'BOM'}[pageno]
            items=take(products,'mate',3,taken,prefer=prefix)
        elif pageno==10:group='asado';items=take(products,'asado',2,taken)
        elif 11<=pageno<=15:group='asado';items=take(products,'asado',3,taken)
        elif 16<=pageno<=18:group='regalos';items=take(products,'regalos',3,taken)
        elif pageno==19:group='regalos';items=take(products,'regalos',3,taken)
        else:group='cierre';items=take(products,'regalos',1,taken)
        pages.append((pageno,group,items))
    pdf=canvas.Canvas(str(PDF),pagesize=A4,pageCompression=1,invariant=1)
    pdf.setTitle('RAÍCES REGALOS · Selección Editorial · Sin Precios')
    for n,group,items in pages:drawing(pdf,items,n,group)
    pdf.save()
    manifest={'source':API,'generated_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'pages':[[{'sku':p['sku'],'name':p['name'],'category':p['group'],'image':p['image'],'source_product_id':p['source_id']} for p in items] for _,_,items in pages]}
    (OUT/'MANIFIESTO_SKU_FOTO.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
    d=fitz.open(PDF);text='\n'.join(x.get_text() for x in d)
    assert len(d)==20,len(d)
    assert not re.search(r'\bARS\b|\$\s*\d|\bprecio\b',text,re.I),'Price content leaked'
    for page_ix,items in enumerate(manifest['pages']):
        t=d[page_ix].get_text().upper()
        for p in items:assert p['sku'].upper() in t,('missing SKU',page_ix+1,p['sku'])
    tiles=[]
    for i,p in enumerate(d):
        pix=p.get_pixmap(matrix=fitz.Matrix(.32,.32),alpha=False)
        image=Image.open(BytesIO(pix.tobytes('png'))).convert('RGB')
        thumbnail=Image.new('RGB',(210,302),'#F1EEE6');image.thumbnail((200,288))
        thumbnail.paste(image,((210-image.width)//2,(302-image.height)//2));tiles.append(thumbnail)
    contact=Image.new('RGB',(210*5,302*4),'#EAE7E0')
    for i,im in enumerate(tiles):contact.paste(im,((i%5)*210,(i//5)*302))
    contact.save(OUT/'VISTA_PREVIA.jpg',quality=89)
    mb=PDF.stat().st_size/1048576
    audit={'pages':len(d),'products':len(taken),'pdf_mib':round(mb,2),'price_tokens_found':False,'sku_text_validation':'PASS','source':'WooCommerce Store API public','visual_review':'PENDING HUMAN REVIEW','original_pdf_reference_comparison':'PENDING blocked source PDFs'}
    (OUT/'INFORME_QA.md').write_text('# Informe de calidad / Raíces\n\n'+json.dumps(audit,indent=2,ensure_ascii=False)+'\n')
    print('PASS',audit,flush=True)
if __name__=='__main__':main()
