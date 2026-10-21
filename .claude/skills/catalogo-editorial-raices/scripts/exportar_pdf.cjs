#!/usr/bin/env node
// Exportación PDF gratuita mediante Playwright. Necesita paquete playwright + navegador Chromium.
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');

async function main() {
  const [inFile, outFile] = process.argv.slice(2);
  if (!inFile || !outFile) {
    console.error('Uso: node exportar_pdf.cjs catalogo.html catalogo.pdf');
    process.exit(2);
  }
  const input = path.resolve(inFile);
  const output = path.resolve(outFile);
  if (!fs.existsSync(input)) throw new Error('HTML de origen no existe: ' + input);
  let playwright;
  try { playwright = require('playwright'); }
  catch(e) { throw new Error('No existe playwright en este entorno. Instálalo en el servidor autorizado (npm install playwright, npx playwright install chromium) o usa la exportación PDF ya disponible.'); }
  fs.mkdirSync(path.dirname(output), {recursive:true});
  const browser = await playwright.chromium.launch({headless:true});
  try {
    const page = await browser.newPage({viewport:{width:1100,height:1600}});
    await page.goto(pathToFileURL(input).href, {waitUntil:'load'});
    await page.evaluate(async () => {
      await document.fonts.ready;
      const imgs = [...document.images];
      await Promise.all(imgs.map(img => img.complete ? Promise.resolve() : new Promise(r => {img.addEventListener('load',r,{once:true}); img.addEventListener('error',r,{once:true});})));
      for (const img of imgs) if (!img.naturalWidth) throw new Error('No cargó la imagen: ' + img.src);
    });
    await page.pdf({path:output, format:'A4', printBackground:true, preferCSSPageSize:true, margin:{top:0,right:0,bottom:0,left:0}});
    console.log('PDF candidato generado:', output);
    console.log('OBLIGATORIO: revisar todas las páginas como imágenes y auditar datos antes de publicar.');
  } finally { await browser.close(); }
}
main().catch(e => {console.error('ERROR:', e.message); process.exitCode=1;});
