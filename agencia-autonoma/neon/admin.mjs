/**
 * Autónoma Dev private administration API.
 * Independent Neon Function: JWT verification + explicit user UUID allowlist.
 * A registered Auth account is NEVER automatically a CRM administrator.
 */
import {createPublicKey,verify} from 'node:crypto';
const ORIGIN='https://autonoma-dev-agencia-v2.onrender.com';
const HEAD={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','Vary':'Origin'};
function answer(body,status=200,extra={}){return new Response(JSON.stringify(body),{status,headers:{...HEAD,...extra}})}
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

let jwks=null,keysCachedAt=0;
async function jwtUser(request){
 const auth=request.headers.get('authorization')||'';
 if(!auth.startsWith('Bearer '))throw new Error('no_bearer');
 const token=auth.slice(7);
 if(token.length>8192)throw new Error('token_too_long');
 const parts=token.split('.');
 if(parts.length!==3)throw new Error('bad_token');
 const header=JSON.parse(Buffer.from(parts[0],'base64url').toString('utf8'));
 const payload=JSON.parse(Buffer.from(parts[1],'base64url').toString('utf8'));
 if(header.alg!=='EdDSA'||!header.kid||typeof header.kid!=='string')throw new Error('bad_algorithm');
 if(!jwks||Date.now()-keysCachedAt>300000){
  const target=new URL(process.env.NEON_AUTH_JWKS_URL||'');
  if(target.protocol!=='https:'||!target.hostname.endsWith('.neon.tech'))throw new Error('jwks_origin');
  const res=await fetch(target,{signal:AbortSignal.timeout(8000)});
  if(!res.ok)throw new Error('jwks_unavailable');
  const data=await res.json();if(!Array.isArray(data.keys))throw new Error('jwks_invalid');
  jwks=data.keys;keysCachedAt=Date.now();
 }
 let key=jwks.find(k=>k.kid===header.kid&&k.kty==='OKP'&&k.crv==='Ed25519'&&k.x);
 if(!key){jwks=null;throw new Error('unknown_key')}
 const valid=verify(null,Buffer.from(parts[0]+'.'+parts[1]),createPublicKey({key,format:'jwk'}),Buffer.from(parts[2],'base64url'));
 const now=Math.floor(Date.now()/1000);
 const issuer=new URL(process.env.NEON_AUTH_BASE_URL||'').origin;
 if(!valid||payload.iss!==issuer||typeof payload.sub!=='string'||payload.sub.length>160||!payload.sub||typeof payload.exp!=='number'||payload.exp<=now||payload.exp>now+3600||typeof payload.iat!=='number'||payload.iat>now+60||(payload.nbf!=null&&payload.nbf>now))throw new Error('invalid_claims');
 return payload.sub;
}
async function checkAdmin(userId){
 const r=await sql('SELECT user_id FROM agencia.admin_users WHERE user_id=$1 AND active=true AND approved_at IS NOT NULL',[userId]);
 return r.length===1;
}
const STATES=new Set(['calificado','descartado','cotizado']);
const CURRENCIES=new Set(['ARS','USD','EUR']);
const MONEY=/^[0-9]{1,11}$/;
export default {
 async fetch(request) {
  const url=new URL(request.url),origin=request.headers.get('origin');
  const cors=origin===ORIGIN?{'Access-Control-Allow-Origin':ORIGIN,'Access-Control-Allow-Headers':'Authorization, Content-Type','Access-Control-Allow-Methods':'GET, POST, OPTIONS','Access-Control-Max-Age':'600'}:{};
  if(request.method==='OPTIONS')return origin===ORIGIN?new Response(null,{status:204,headers:{...HEAD,...cors}}):answer({error:'forbidden'},403);
  if(origin!==ORIGIN)return answer({error:'forbidden'},403);
  let user;
  try{user=await jwtUser(request)}catch{return answer({error:'unauthorized'},401,cors)}
  try{if(!await checkAdmin(user))return answer({error:'not_authorized_as_owner'},403,cors)}catch{return answer({error:'backend_unavailable'},503,cors)}
  try{
    if(url.pathname==='/api/admin/leads'&&request.method==='GET'){
      const rows=await sql(`SELECT l.id::text,l.created_at,l.name,l.email,l.business,l.service,l.details,l.budget,l.score,l.risk_flags,l.status,l.client_country,l.preferred_currency,l.preferred_language,l.budget_range_global,
       q.id::text AS quote_id,q.stage AS quote_stage,q.quote_currency,q.quote_amount_minor,q.approved_at
       FROM agencia.leads l LEFT JOIN LATERAL (SELECT * FROM agencia.quote_drafts WHERE lead_id=l.id ORDER BY created_at DESC LIMIT 1) q ON true
       WHERE l.source='neon-web'
       ORDER BY l.created_at DESC LIMIT 100`);
      return answer({ok:true,leads:rows},200,cors);
    }
    if(request.method==='GET'&&url.pathname==='/api/admin/metrics'){
      const rows=await sql(`SELECT count(*) FILTER (WHERE status='nuevo')::integer AS nuevos,count(*) FILTER (WHERE status='calificado')::integer AS calificados,count(*) FILTER (WHERE preferred_currency='USD')::integer AS usd,count(*) FILTER (WHERE preferred_currency='EUR')::integer AS eur,count(*)::integer AS total FROM agencia.leads WHERE source='neon-web'`);
      return answer({ok:true,metrics:rows[0]},200,cors);
    }
    if(request.method==='POST'&&url.pathname==='/api/admin/lead/status'){
      const body=await request.text();if(body.length>2200)return answer({error:'too_large'},413,cors);
      let v;try{v=JSON.parse(body)}catch{return answer({error:'bad_json'},400,cors)}
      if(!/^[0-9a-f-]{36}$/i.test(v.id||'')||!STATES.has(v.status))return answer({error:'invalid_request'},400,cors);
      const rows=await sql(`WITH updated AS (
       UPDATE agencia.leads SET status=$2
       WHERE id=$1::uuid AND source='neon-web' AND ( (status='nuevo' AND $2 IN ('calificado','descartado')) OR (status='calificado' AND $2 IN ('cotizado','descartado')) )
       RETURNING id,status
      ) SELECT id::text,status FROM updated`,[v.id,v.status]);
      return rows.length?answer({ok:true,status:rows[0].status},200,cors):answer({error:'transition_not_allowed'},409,cors);
    }
    if(request.method==='POST'&&url.pathname==='/api/admin/quote/review'){
      const body=await request.text();if(body.length>2200)return answer({error:'too_large'},413,cors);
      let v;try{v=JSON.parse(body)}catch{return answer({error:'bad_json'},400,cors)}
      if(!/^[0-9a-f-]{36}$/i.test(v.id||'')||!CURRENCIES.has(v.currency)||!MONEY.test(String(v.amount_minor??''))||!['revision','aprobado'].includes(v.stage))return answer({error:'invalid_quote'},400,cors);
      const amount=Number(v.amount_minor);if(!Number.isSafeInteger(amount)||amount<1||amount>100000000000)return answer({error:'amount_limit'},400,cors);
      const rows=await sql(`WITH upd AS (
        UPDATE agencia.quote_drafts q SET
          quote_currency=$2,quote_amount_minor=$3::bigint,stage=$4,
          approved_by=CASE WHEN $4='aprobado' THEN $5 ELSE NULL END,
          approved_at=CASE WHEN $4='aprobado' THEN now() ELSE NULL END
        WHERE q.id=$1::uuid
          AND q.stage IN ('borrador','revision') AND (q.stage='borrador' OR $4='aprobado')
          AND EXISTS(SELECT 1 FROM agencia.leads l WHERE l.id=q.lead_id AND l.source='neon-web' AND l.preferred_currency=$2)
        RETURNING q.id,q.lead_id,q.stage
      ), event AS (
        INSERT INTO agencia.events(lead_id,event_type,actor,data)
        SELECT lead_id,'quote_reviewed',$5,jsonb_build_object('stage',stage,'currency',$2,'amount_minor',$3::bigint)
        FROM upd RETURNING id
      ) SELECT id::text,stage FROM upd`,[v.id,v.currency,String(amount),v.stage,user]);
      return rows.length?answer({ok:true,stage:rows[0].stage},200,cors):answer({error:'quote_review_denied'},409,cors);
    }
    return answer({error:'not_found'},404,cors);
  }catch(e){console.error('admin_error',e?.name||'unknown');return answer({error:'backend_unavailable'},503,cors)}
 }
};
