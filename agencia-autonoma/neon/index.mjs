/**
 * Autónoma Dev intake backend. Neon Functions (Node 24).
 * No dependencies, no external AI charges; database URL injected by Neon.
 * Separate "agencia" schema only. Never send credentials to the browser.
 */
const ALLOWED_ORIGIN = 'https://autonoma-dev-agencia.onrender.com';
const SERVICES = {
  web: { label:'Web comercial',min:120000,max:280000 },
  automatizacion: { label:'Automatización',min:180000,max:550000 },
  aplicacion: { label:'Sistema personalizado',min:350000,max:950000 },
  mantenimiento: { label:'Soporte mensual',min:45000,max:150000 },
  otro: { label:'Diagnóstico',min:null,max:null },
};
const BUDGETS = new Set(['no_definido','hasta_150k','150k_500k','mas_500k']);
const HEADERS = { 'content-type':'application/json; charset=utf-8','cache-control':'no-store' };
const respond = (v,status,extra={}) => new Response(JSON.stringify(v),{status,headers:{...HEADERS,...extra}});
const clean = (v,max) => typeof v==='string' ? v.trim().slice(0,max+1) : '';
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/** Authenticated server-to-Neon SQL over TLS; parameters never interpolated. */
async function sql(query,params=[]) {
  const connectionString=process.env.DATABASE_URL;
  if(!connectionString) throw new Error('database_missing');
  const uri=new URL(connectionString);
  if(!(uri.protocol==='postgres:'||uri.protocol==='postgresql:') ||
     !/^[a-z0-9.-]+\.neon\.tech$/i.test(uri.hostname)) throw new Error('invalid_database_target');
  const res=await fetch('https://'+uri.hostname+'/sql',{
    method:'POST',
    headers:{
      'Neon-Connection-String':connectionString,
      'Neon-Array-Mode':'true',
      'Neon-Raw-Text-Output':'true',
      'Content-Type':'application/json'
    },
    body:JSON.stringify({query,params}),
    signal:AbortSignal.timeout(12000)
  });
  if(!res.ok) { console.error('sql_status',res.status);throw new Error('database_unavailable'); }
  const raw=await res.json();
  if(!Array.isArray(raw.fields)||!Array.isArray(raw.rows))throw new Error('unexpected_db_result');
  return raw.rows.map(row=>Object.fromEntries(raw.fields.map((field,i)=>[field.name,row[i]])));
}
function assess(input) {
  let flags=[];
  if(input.details.length<60) flags.push('brief_corto');
  if(/\b(paciente|diagn[oó]stico|historia cl[ií]nica|ni[ñn]os|biom[eé]tricos)\b/i.test(input.details)) flags.push('datos_sensibles');
  if(/\b(spam|scraping masivo|correo masivo|bases de datos compradas)\b/i.test(input.details)) flags.push('riesgo_abuso');
  const selected=SERVICES[input.service];
  if(input.budget==='hasta_150k' && selected.min>150000) flags.push('presupuesto_inferior_al_rango');
  const score=Math.max(10,Math.min(90,45+(input.business?10:0)+(input.budget!=='no_definido'?10:0)+(input.details.length>140?10:0)-flags.length*8));
  return {score,flags,min:selected.min,max:selected.max};
}
function parse(data) {
  if(!data||typeof data!=='object'||Array.isArray(data))return null;
  const v={
    name:clean(data.name,90), email:clean(data.email,200).toLowerCase(),
    business:clean(data.business??'',120), service:clean(data.service,40),
    budget:clean(data.budget,40), details:clean(data.details,2500),
    honey:clean(data.honey??'',200), consent:data.consent===true
  };
  if(v.name.length<2||!EMAIL.test(v.email)||v.email.length>200||v.business.length>120
    ||v.details.length<20||v.details.length>2500||!SERVICES[v.service]||!BUDGETS.has(v.budget)||!v.consent)return null;
  return v;
}
export default {
 async fetch(req) {
  const url=new URL(req.url), origin=req.headers.get('origin');
  const cors = origin===ALLOWED_ORIGIN ? {
    'Access-Control-Allow-Origin':ALLOWED_ORIGIN,
    'Access-Control-Allow-Methods':'POST, OPTIONS',
    'Access-Control-Allow-Headers':'Content-Type',
    'Access-Control-Max-Age':'600',
    'Vary':'Origin'
  } : {'Vary':'Origin'};
  if(req.method==='OPTIONS') return new Response(null,{status:204,headers:cors});
  if(url.pathname==='/health'&&req.method==='GET')return respond({ok:true,service:'autonoma-dev-intake',database:'configured'},200,cors);
  if(url.pathname!=='/api/lead'||req.method!=='POST')return respond({error:'not_found'},404,cors);
  if(origin!==ALLOWED_ORIGIN)return respond({error:'origin_rejected'},403,cors);
  const ct=req.headers.get('content-type')??'';
  if(!ct.includes('application/json'))return respond({error:'content_type_required'},415,cors);
  const body=await req.text();
  if(body.length>12000)return respond({error:'too_large'},413,cors);
  let input;
  try{input=parse(JSON.parse(body));}catch{return respond({error:'invalid_json'},400,cors);}
  if(!input)return respond({error:'invalid_fields'},400,cors);
  if(input.honey)return respond({ok:true,reference:'RECIBIDO'},202,cors);
  try{
    const t=assess(input);
    // Parameterized, single-statement atomic write: duplicate + global load gate.
    const rows=await sql(`
      WITH gate AS (
        SELECT (
          (SELECT count(*) FROM agencia.leads WHERE created_at>now()-interval '10 minutes')<30
          AND NOT EXISTS(SELECT 1 FROM agencia.leads WHERE email=$2 AND created_at>now()-interval '15 minutes')
        ) AS permitted
      ),
      inserted AS (
        INSERT INTO agencia.leads(name,email,business,service,budget,details,consent_at,score,risk_flags,estimate_min_ars,estimate_max_ars,source)
        SELECT $1,$2,$3,$4,$5,$6,now(),$7::smallint,$8::jsonb,$9::integer,$10::integer,'neon-web'
        FROM gate WHERE permitted
        RETURNING id
      ),
      audit AS (
        INSERT INTO agencia.events(lead_id,event_type,actor,data)
        SELECT id,'lead_received','system',jsonb_build_object('rules','v1','needs_review',true)
        FROM inserted
        RETURNING id
      )
      SELECT id::text FROM inserted
    `,[input.name,input.email,input.business||null,input.service,input.budget,input.details,t.score,JSON.stringify(t.flags),t.min,t.max]);
    if(rows.length===0)return respond({error:'recent_submission_or_rate_limit'},429,cors);
    return respond({ok:true,reference:rows[0].id},201,cors);
  }catch(error){
    console.error('agency_intake_error',error instanceof Error?error.name:'unknown');
    return respond({error:'temporary_error'},503,cors);
  }
 }
};
