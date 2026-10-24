import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const read=rel=>readFileSync(new URL(rel,import.meta.url),'utf8');
const base='https://autonoma-dev-agencia-v2.onrender.com';
const sitemap=read('../site/sitemap.xml');
const home=read('../site/index.html');
for(const [slug,service,word] of [
 ['automatizaciones','automatizacion','Automatización'],
 ['desarrollo-web','web','Páginas web']
]){
 test('service page '+slug+' has unique Spanish SEO metadata and no invented success story',()=>{
  const page=read('../site/'+slug+'/index.html');
  assert.match(page,/<html lang="es-AR">/);
  assert.match(page,/<meta name="description" content="[^"]{90,190}"/);
  assert.ok(page.includes('<link rel="canonical" href="'+base+'/'+slug+'/">'));
  assert.ok(page.includes('<title>')&&page.includes(word));
  assert.ok(page.includes('href="/?servicio='+service+'#contacto"'));
  assert.ok(!/<script\\b/i.test(page));
  assert.ok(!/testimonios de clientes satisfechos|clientes felices|más de 100 clientes/i.test(page));
  assert.ok(page.includes('no son testimonios ni trabajos de clientes'));
 });
 test('sitemap and home point to '+slug,()=>{
  assert.ok(sitemap.includes('<loc>'+base+'/'+slug+'/</loc>'));
  assert.ok(home.includes('href="/'+slug+'/">'));
 });
}
test('contact form only preselects known service names from trusted constants',()=>{
 assert.ok(home.includes("new URLSearchParams(window.location.search).get('servicio')"));
 assert.ok(home.includes("['web','automatizacion','aplicacion','mantenimiento','otro'].includes(serviceFromPage)"));
 assert.ok(home.includes("serviceControl.value=serviceFromPage"));
});
test('sitemap has no duplicate URLs and keeps original home and privacy',()=>{
 const names=[...sitemap.matchAll(/<loc>(.*?)<\\/loc>/g)].map(x=>x[1]);
 assert.equal(new Set(names).size,names.length);
 assert.ok(names.includes(base+'/'));
 assert.ok(names.includes(base+'/privacidad/'));
});
