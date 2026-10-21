#!/usr/bin/env python3
"""Raices Regalos catalog, built only from actual public product pages/photos."""
from __future__ import annotations
import concurrent.futures as cf
import hashlib, io, json, os, re, sys, time
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageOps, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import fitz
from editorial import (COVER_TITLE, COVER_SUBTITLE, COLLECTION_LINE,
    OPENING_TEXT, DARK_SECTION, COLOR_SECTION, FOOTER_TEXT)

BASE = "https://raicesregalos.com"
ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
CACHE = ROOT / "_images"
DIST.mkdir(exist_ok=True)
CACHE.mkdir(exist_ok=True)
AGENT = requests.Session()
AGENT.headers.update({"User-Agent": "Mozilla/5.0 (compatible; RaicesCatalog/1.0)",
                      "Accept-Language": "es-AR,es;q=0.9"})
CAT = [
 ("Mates", "/categoria-producto/mates/", 38),
 ("Sets de mate", "/categoria-producto/mate/", 30),
 ("Asado", "/categoria-producto/set-de-asado/", 31),
 ("Bolsos", "/categoria-producto/bolsos-y-mochilas/", 18),
 ("Accesorios", "/categoria-producto/billeteras-y-accesorios/", 18),
 ("Cuchillos", "/categoria-producto/cuchillos/", 9),
 ("Bombillas", "/categoria-producto/bombillas/", 8),
]
W,H = A4
M = 46

def get(url, max_tries=3):
    for attempt in range(max_tries):
        try:
            r = AGENT.get(url, timeout=20, allow_redirects=True)
            if r.ok and len(r.content)>100:
                return r
        except requests.RequestException:
            pass
        time.sleep(0.45 + attempt*.65)
    return None

def candidate_urls():
    seen={}
    for category, path, max_items in CAT:
        pages=0; found=0
        while pages<5 and found<max_items:
            pages+=1
            url=BASE+path+(f"page/{pages}/" if pages>1 else "")
            r=get(url)
            if not r: break
            doc=BeautifulSoup(r.text,"html.parser")
            old=len(seen)
            for a in doc.select("a[href*='/producto/']"):
                href=a.get("href","").split("?")[0].split("#")[0]
                if href.startswith("/") : href=BASE+href
                if not (href.startswith(BASE+"/producto/") and
                   re.fullmatch(r"https://raicesregalos\.com/producto/[^/?#]+/?",href)): continue
                if href not in seen:
                    seen[href]=category
                    found+=1
                    if found>=max_items: break
            if len(seen)==old and pages>1: break
    print("Candidate product pages:",len(seen), flush=True)
    return list(seen.items())

def safe_title(raw):
    raw=re.sub(r"\s+"," ",raw).strip()
    raw=re.sub(r"\s*-\s*(Mayorista|Raices Regalos).*$","",raw, flags=re.I)
    raw=re.sub(r"[-_]?\b(?:SET|MAT|CUE)\d+[A-Z0-9-]*$","",raw,flags=re.I)
    return raw[:78].strip(" -|")

def fetch_product(item):
    url,category=item
    try:
        r=get(url,2)
        if not r: return None
        doc=BeautifulSoup(r.text,"html.parser")
        h=doc.find("h1")
        title=safe_title(h.get_text(" ",strip=True) if h else "")
        if not title: return None
        sku=doc.select_one(".sku")
        sku=(sku.get_text(" ",strip=True) if sku else "").strip()
        if not sku:
            match=re.search(r"\bSKU\s*:\s*([A-Za-z][A-Za-z0-9_-]{3,30})",doc.get_text(" ",strip=True),re.I)
            sku=match.group(1) if match else ""
        sku=re.sub(r"[^a-zA-Z0-9_-]","",sku.upper())[:24]
        if len(sku)<4: return None
        imeta=doc.select_one('meta[property="og:image"]')
        image_url=(imeta.get("content","") if imeta else "").strip()
        if not image_url.startswith(BASE+"/wp-content/uploads/"): 
            main=doc.select_one(".woocommerce-product-gallery__image img")
            image_url=main.get("data-large_image","") if main else ""
        if not image_url.startswith(BASE+"/wp-content/uploads/"): return None
        img_resp=get(image_url,2)
        if not img_resp: return None
        data=img_resp.content
        im=Image.open(io.BytesIO(data))
        im.load()
        if min(im.size)<280: return None
        if im.mode not in ("RGB","RGBA"): im=im.convert("RGB")
        im.thumbnail((960,960),Image.Resampling.LANCZOS)
        path=CACHE/(hashlib.sha256(data).hexdigest()[:24]+".jpg")
        if not path.exists():
            rgb=Image.new("RGB",im.size,"white")
            if im.mode=="RGBA": rgb.paste(im,mask=im.getchannel("A"))
            else: rgb.paste(im)
            rgb.save(path,format="JPEG",quality=87,subsampling=0)
        pix=im.convert("RGB").resize((72,72)).getdata()
        nonwhite=[]; colorful=0; earthy=0; dark=0
        for rr,gg,bb in pix:
            if min(rr,gg,bb)>231: continue
            mx=max(rr,gg,bb); mn=min(rr,gg,bb)
            sat=(mx-mn)/max(mx,1)
            if mx<120: dark+=1
            if rr>gg*1.13 and gg>bb*.85 and 40<rr<230: earthy+=1
            if sat>.36 and mx>110 and not (rr>gg*1.15 and gg>=bb*.85): colorful+=1
            nonwhite.append(1)
        total=max(1,len(nonwhite))
        flavor="color" if colorful/total>.18 else "dark" if (earthy+dark)/total>.37 else "neutral"
        return dict(title=title,sku=sku,category=category,url=url,
                    image_url=image_url,image=str(path),tone=flavor,
                    sha256=hashlib.sha256(data).hexdigest(),size=im.size)
    except Exception as ex:
        print("skip",url,str(ex)[:75],flush=True)
        return None

def font_file(name):
    roots=["/usr/share/fonts/truetype/lato/","/usr/share/fonts/truetype/dejavu/",
           "/usr/share/fonts/truetype/liberation2/"]
    options={"regular":["Lato-Regular.ttf","DejaVuSans.ttf","LiberationSans-Regular.ttf"],
             "bold":["Lato-Heavy.ttf","DejaVuSans-Bold.ttf","LiberationSans-Bold.ttf"],
             "light":["Lato-Light.ttf","DejaVuSans-ExtraLight.ttf","LiberationSans-Regular.ttf"]}
    for fn in options[name]:
        for root in roots:
            p=Path(root)/fn
            if p.exists(): return str(p)
    raise RuntimeError("No suitable PDF font found")

def register_fonts():
    for name in ("regular","bold","light"):
        pdfmetrics.registerFont(TTFont("RR-"+name,font_file(name)))

def txt(c,x,y,text,size=10,color="#171717",font="regular"):
    c.setFillColor(color);c.setFont("RR-"+font,size)
    c.drawString(x,y,str(text))

def fitline(text,max_width,font="bold",size=13):
    words=text.split();lines=[];line=""
    for word in words:
        trial=(line+" "+word).strip()
        if pdfmetrics.stringWidth(trial,"RR-"+font,size)>max_width and line:
            lines.append(line);line=word
        else: line=trial
    if line:lines.append(line)
    return lines[:2] if len(lines)<3 else [lines[0],lines[1].rstrip(" .")+"…"]

def image_contain(c,img_path,x,y,w,h):
    im=Image.open(img_path)
    iw,ih=im.size
    scale=min(w/iw,h/ih)
    aw,ah=iw*scale,ih*scale
    c.drawImage(str(img_path),x+(w-aw)/2,y+(h-ah)/2,aw,ah,mask="auto")

def product(c,p,x,y,image_w=236,image_h=180):
    # Real photograph, deliberately without cards, borders or shadows.
    image_contain(c,p["image"],x,y,image_w,image_h)
    lines=fitline(p["title"],image_w,"bold",11.8)
    for j,s in enumerate(lines):
        txt(c,x,y-22-j*15,s,11.8,"#111111","bold")
    txt(c,x,y-31-len(lines)*15,p["sku"],9.5,"#777777","regular")
    txt(c,x,y-49-len(lines)*15,p["category"].upper(),7.4,"#929292","regular")
    c.linkURL(p["url"],(x,y-62-len(lines)*15,x+image_w,y+image_h),relative=0,thickness=0)

def cover(c,first,second,count):
    c.setFillColorRGB(1,1,1);c.rect(0,0,W,H,fill=1,stroke=0)
    txt(c,M,H-65,"RAÍCES",30,"#111111","bold")
    txt(c,M+1,H-84,"REGALOS",11,"#777777","regular")
    txt(c,W-204,H-66,"CATÁLOGO  /  COLECCIÓN 2026",9,"#565656","bold")
    c.setStrokeColorRGB(.10,.10,.10);c.setLineWidth(.85);c.line(M,H-101,W-M,H-101)
    txt(c,M,H-175,"OBJETOS PARA",45,"#111111","bold")
    txt(c,M,H-228,"COMPARTIR",49,"#111111","bold")
    txt(c,M,H-266,COVER_SUBTITLE[:76],12,"#5A5A5A","regular")
    image_contain(c,first["image"],250,174,293,354)
    if second:image_contain(c,second["image"],M+3,205,185,211)
    c.setStrokeColorRGB(.83,.83,.83);c.setLineWidth(.55);c.line(M,134,W-M,134)
    txt(c,M,110,"MATES   /   ASADO   /   REGALOS   /   ACCESORIOS",10.2,"#181818","bold")
    txt(c,M,87,"FOTOGRAFÍAS REALES DE PRODUCTOS",8.2,"#777777","regular")
    txt(c,W-107,81,"2026",29,"#181818","bold")
    c.setStrokeColorRGB(.86,.86,.86);c.line(M,57,W-M,57)
    txt(c,M,35,"CATÁLOGO SIN PRECIOS",8.2,"#767676")
    txt(c,W-170,35,"raicesregalos.com",9.3,"#4F4F4F")
    c.showPage()

def page(c,items,page_no,count,tone):
    c.setFillColorRGB(1,1,1);c.rect(0,0,W,H,fill=1,stroke=0)
    txt(c,M,H-52,"RAÍCES",15,"#191919","bold")
    txt(c,M+76,H-52,"REGALOS",9,"#777777","regular")
    txt(c,W-160,H-51,"COLECCIÓN  /  2026",9.2,"#757575")
    c.setStrokeColorRGB(.84,.84,.84);c.setLineWidth(.65);c.line(M,H-66,W-M,H-66)
    txt(c,M,H-105,"SELECCIÓN  /  %02d"%(page_no-1),9.5,"#6E6E6E","bold")
    dark=sum(1 for p in items if p["tone"]=="dark")
    color=sum(1 for p in items if p["tone"]=="color")
    cats=list(dict.fromkeys(p["category"] for p in items))
    counts={category:sum(p["category"]==category for p in items) for category in cats}
    primary=max(cats,key=lambda cat:counts[cat]) if cats else "Mates"
    groups={"Mates":"MATES","Sets de mate":"SETS DE MATE",
            "Asado":"PARA EL ASADO","Bolsos":"BOLSOS Y MOCHILAS",
            "Accesorios":"ACCESORIOS","Cuchillos":"CUCHILLOS",
            "Bombillas":"BOMBILLAS"}
    title=("COLOR Y CARÁCTER" if color>=2 and len(cats)>1 else
           groups.get(primary,"NUESTRA SELECCIÓN") if counts.get(primary,0)>=2
           else "NUESTRA SELECCIÓN")
    txt(c,M,H-153,title,29,"#141414","bold")
    subtitle=(" / ".join(cats[:3]) if len(cats)>1 else "SELECCIÓN RAÍCES 2026")
    txt(c,M,H-179,subtitle.upper(),9.2,"#686868","regular")
    c.setStrokeColorRGB(.90,.90,.90);c.line(M,H-194,W-M,H-194)
    if len(items)>0:product(c,items[0],M,415,image_w=234,image_h=181)
    if len(items)>1:product(c,items[1],309,415,image_w=237,image_h=181)
    if len(items)>2:product(c,items[2],M,155,image_w=234,image_h=181)
    if len(items)>3:product(c,items[3],309,155,image_w=237,image_h=181)
    c.setStrokeColorRGB(.85,.85,.85);c.setLineWidth(.55);c.line(M,39,W-M,39)
    txt(c,M,23,"RAÍCES REGALOS   ·   CATÁLOGO SIN PRECIOS",8,"#757575")
    txt(c,W-88,23,"%02d / %02d"%(page_no,1+(count+3)//4),8.5,"#757575","bold")
    c.showPage()

def make_preview(pdf,out):
    doc=fitz.open(pdf)
    take=[0,1,min(len(doc)-1,3),min(len(doc)-1,round(len(doc)*.6))]
    imgs=[]
    for idx in take:
        pg=doc[idx]; pix=pg.get_pixmap(matrix=fitz.Matrix(.88,.88),alpha=False)
        im=Image.frombytes("RGB",(pix.width,pix.height),pix.samples)
        imgs.append(im)
    pad=20;tw=imgs[0].width;th=imgs[0].height
    sheet=Image.new("RGB",(tw*2+pad*3,th*2+pad*3),"#e7e7e7")
    for i,im in enumerate(imgs):
        sheet.paste(im,(pad+(i%2)*(tw+pad),pad+(i//2)*(th+pad)))
    sheet.save(out,optimize=True)

def run():
    candidates=candidate_urls()
    if len(candidates)<40:raise RuntimeError("Insufficient official category listings")
    products=[]
    with cf.ThreadPoolExecutor(max_workers=7) as pool:
        futures={pool.submit(fetch_product,p):p for p in candidates[:185]}
        for n,f in enumerate(cf.as_completed(futures)):
            p=f.result()
            if p:products.append(p)
            if n%25==0:print("Verified products:",len(products),"of",n+1,flush=True)
    # Remove duplicates by exact SKU and photo digest.
    unique={};seenimgs=set()
    for p in sorted(products,key=lambda v:(v["category"],v["sku"],v["url"])):
        if p["sku"] not in unique and p["sha256"] not in seenimgs:
            unique[p["sku"]]=p;seenimgs.add(p["sha256"])
    products=list(unique.values())
    if len(products)<45:raise RuntimeError(f"Only {len(products)} verified items; refuse an incomplete catalog")
    quotas={"Mates":23,"Sets de mate":23,"Asado":21,"Bolsos":9,"Accesorios":8,"Cuchillos":5,"Bombillas":5}
    kept=[];bycat=defaultdict(list)
    for p in products:bycat[p["category"]].append(p)
    for name,_,__ in CAT:
        values=sorted(bycat[name],key=lambda p:({"dark":0,"neutral":1,"color":2}[p["tone"]],p["sku"]))
        kept.extend(values[:quotas[name]])
    leftovers=[p for p in products if p not in kept]
    kept.extend(leftovers[:max(0,96-len(kept))])
    kept=kept[:96]
    kept.sort(key=lambda p:({"dark":0,"neutral":1,"color":2}[p["tone"]],
                            list(quotas).index(p["category"]) if p["category"] in quotas else 99,p["sku"]))
    # No more than 24 four-photo pages + the cover.
    register_fonts()
    target=DIST/"Raices_Regalos_Catalogo_2026_Editorial_V2.pdf"
    pdf=canvas.Canvas(str(target),pagesize=A4,pageCompression=1)
    pdf.setTitle("Raíces Regalos | Catálogo editorial sin precios | 2026")
    pdf.setAuthor("Raíces Regalos")
    cover(pdf,kept[0],kept[min(14,len(kept)-1)],len(kept))
    for n in range(0,len(kept),4):
        batch=kept[n:n+4]
        tone=batch[0]["tone"]
        page(pdf,batch,2+n//4,len(kept),tone)
    pdf.save()
    doc=fitz.open(target)
    if len(doc)>25:raise RuntimeError("Exceeded 25-page limit")
    if len(doc)<12:raise RuntimeError("Fewer than 12 pages: catalog too short")
    if any(("Precio por" in p.get_text() or re.search(r"\$\s*\d",p.get_text())) for p in doc):
        raise RuntimeError("Prices leaked into PDF")
    if any(not p.get_images() for p in doc):raise RuntimeError("Empty photographic page found")
    manifest={"source":"raicesregalos.com/producto/","verified_count":len(kept),
      "pages":len(doc),"date":date.today().isoformat(),
      "catalog_path":target.name,"products":kept,
      "policy":"Each item, SKU, photo and source URL retrieved from Raices public pages; no AI product renders."}
    (DIST/"trazabilidad_productos.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    make_preview(target,DIST/"vista_previa_4_paginas.png")
    print("SUCCESS",target,"pages",len(doc),"products",len(kept),flush=True)
if __name__=="__main__":run()
