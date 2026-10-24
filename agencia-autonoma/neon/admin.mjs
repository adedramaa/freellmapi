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
 const r=await sql(`SELECT a.user_id FROM agencia.admin_users a
  JOIN neon_auth."user" u ON u.id::text=a.user_id
  WHERE a.user_id=$1 AND a.active=true AND a.approved_at IS NOT NULL
    AND u."emailVerified"=true AND COALESCE(u."banned",false)=false`,[userId]);
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
  let approved;
  try{approved=await checkAdmin(user)}catch{return answer({error:'backend_unavailable'},503,cors)}
  // Safe onboarding: reveal the authenticated user's own ID and approval flag only.
  // This endpoint never returns customer records or allows self-approval.
  if(request.method==='GET'&&url.pathname==='/api/admin/access')
    return answer({ok:true,user_id:user,approved},200,cors);
  // An owner claim is permitted only for the specifically preauthorized pending identity,
  // after trusted Neon Auth has verified the same original mailbox. No email address or
  // OTP is accepted from the client. This does not grant rights to arbitrary signups.
  if(request.method==='POST'&&url.pathname==='/api/admin/claim-owner'){
    try{
      const rows=await sql(`
        WITH verified_candidate AS (
          SELECT a.user_id FROM agencia.admin_users a
          JOIN neon_auth."user" u ON u.id::text=a.user_id
          WHERE a.user_id=$1 AND a.active=false AND a.approved_at IS NULL
            AND a.approved_by=('pending_email_sha256:' ||
                 encode(sha256(convert_to(lower(u.email),'UTF8')),'hex'))
            AND u."emailVerified"=true AND COALESCE(u."banned",false)=false
            AND NOT EXISTS (SELECT 1 FROM agencia.admin_users existing WHERE existing.active=true)
        ), accepted AS (
          UPDATE agencia.admin_users a SET active=true,approved_at=now(),
            approved_by='owner_verified_email_claim'
          WHERE a.user_id IN (SELECT user_id FROM verified_candidate)
            AND a.active=false AND a.approved_at IS NULL
          RETURNING a.user_id
        ) SELECT user_id FROM accepted
      `,[user]);
      return rows.length===1
        ?answer({ok:true,approved:true},200,cors)
        :answer({error:'owner_identity_not_verified_or_not_preapproved'},403,cors);
    }catch{
      return answer({error:'claim_unavailable'},503,cors);
    }
  }
  if(!approved)return answer({error:'not_authorized_as_owner'},403,cors);
  try{
    if(url.pathname==='/api/admin/leads'&&request.method==='GET'){
      const rows=await sql(`SELECT l.id::text,l.created_at,l.name,l.email,l.business,l.service,l.details,l.budget,l.score,l.risk_flags,l.status,l.client_country,l.preferred_currency,l.preferred_language,l.budget_range_global,
       q.id::text AS quote_id,q.stage AS quote_stage,q.quote_currency,q.quote_amount_minor,q.approved_at,
       q.scope_json->>'alcance_acordado' AS quote_scope,
       q.scope_json->>'entregables' AS quote_deliverables,
       q.scope_json->>'exclusiones' AS quote_exclusions,
       q.scope_json->>'plazo_dias' AS quote_days,
       q.scope_json->>'revisiones_incluidas' AS quote_revisions,
       pay.id::text AS payment_draft_id,pay.provider AS payment_method,pay.state AS payment_state,
       comm.content AS reply_draft
       FROM agencia.leads l LEFT JOIN LATERAL (SELECT * FROM agencia.quote_drafts WHERE lead_id=l.id ORDER BY created_at DESC LIMIT 1) q ON true
       LEFT JOIN LATERAL (SELECT content FROM agencia.client_communications WHERE lead_id=l.id AND kind='reply_draft' ORDER BY created_at DESC LIMIT 1) comm ON true
       LEFT JOIN LATERAL (SELECT id,provider,state FROM agencia.payment_intents WHERE lead_id=l.id AND state NOT IN ('cancelled','rejected','refunded') ORDER BY created_at DESC LIMIT 1) pay ON true
       WHERE l.source='neon-web'
       ORDER BY l.created_at DESC LIMIT 100`);
      return answer({ok:true,leads:rows},200,cors);
    }
    if(request.method==='GET'&&url.pathname==='/api/admin/metrics'){
      const rows=await sql(`SELECT count(*) FILTER (WHERE status='nuevo')::integer AS nuevos,count(*) FILTER (WHERE status='calificado')::integer AS calificados,count(*) FILTER (WHERE preferred_currency='USD')::integer AS usd,count(*) FILTER (WHERE preferred_currency='EUR')::integer AS eur,count(*)::integer AS total FROM agencia.leads WHERE source='neon-web'`);
      const monitor=await sql('SELECT slot,checked_at,website_ok,backend_ok,pending_leads,total_leads FROM agencia.monitor_snapshots ORDER BY checked_at DESC LIMIT 1');
      const monitorEvents=await sql("SELECT slot,event_key,previous_value,current_value,details FROM agencia.monitor_events WHERE slot>now()-interval '7 days' ORDER BY slot DESC,event_key ASC LIMIT 12");
      return answer({ok:true,metrics:rows[0],monitor:monitor[0]||null,monitor_events:monitorEvents},200,cors);
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
      const body=await request.text();if(body.length>6000)return answer({error:'too_large'},413,cors);
      let v;try{v=JSON.parse(body)}catch{return answer({error:'bad_json'},400,cors)}
      if(!/^[0-9a-f-]{36}$/i.test(v.id||'')||!CURRENCIES.has(v.currency)||!MONEY.test(String(v.amount_minor??''))||!['revision','aprobado'].includes(v.stage))return answer({error:'invalid_quote'},400,cors);
      const amount=Number(v.amount_minor);if(!Number.isSafeInteger(amount)||amount<1||amount>100000000000)return answer({error:'amount_limit'},400,cors);
      const scope=typeof v.scope==='string'?v.scope.trim():'';
      const deliverables=typeof v.deliverables==='string'?v.deliverables.trim():'';
      const exclusions=typeof v.exclusions==='string'?v.exclusions.trim():'';
      const days=Number(v.delivery_days),revisions=Number(v.revisions);
      if(scope.length<25||scope.length>1200||deliverables.length<12||deliverables.length>800||
        exclusions.length>500||!Number.isInteger(days)||days<1||days>180||
        !Number.isInteger(revisions)||revisions<0||revisions>8) return answer({error:'scope_incomplete'},400,cors);
      if(v.stage==='aprobado' && (deliverables.length<20 || exclusions.length<10))
        return answer({error:'approval_requires_scope_and_exclusions'},400,cors);
      const rows=await sql(`WITH upd AS (
        UPDATE agencia.quote_drafts q SET
          quote_currency=$2,quote_amount_minor=$3::bigint,stage=$4,
          scope_json=q.scope_json || jsonb_build_object('alcance_acordado',$6,'entregables',$7,'exclusiones',$8,'plazo_dias',$9::integer,'revisiones_incluidas',$10::integer,'es_precio_final',false,'requiere_revision_humana',true),
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
      ) SELECT id::text,stage FROM upd`,[v.id,v.currency,String(amount),v.stage,user,scope,deliverables,exclusions,days,revisions]);
      return rows.length?answer({ok:true,stage:rows[0].stage},200,cors):answer({error:'quote_review_denied'},409,cors);
    }
    if(request.method==='POST'&&url.pathname==='/api/admin/quote/mark-sent'){
      const raw=await request.text();if(raw.length>1500)return answer({error:'too_large'},413,cors);
      let v;try{v=JSON.parse(raw)}catch{return answer({error:'bad_json'},400,cors)}
      if(!/^[0-9a-f-]{36}$/i.test(v?.quote_id||'')||
          typeof v?.reference!=='string'||v.reference.trim().length<8||v.reference.length>190)
        return answer({error:'reference_required'},400,cors);
      const rows=await sql('SELECT agencia.mark_quote_sent_manual($1::uuid,$2::text,$3::text) AS recorded',
        [v.quote_id,user,v.reference.trim()]);
      return rows[0]?.recorded === true||rows[0]?.recorded === 't'
        ?answer({ok:true,stage:'enviado',actual_delivery:'manual_attestation'},200,cors)
        :answer({error:'quote_not_eligible'},409,cors);
    }
    if(request.method==='POST'&&url.pathname==='/api/admin/quote/accept'){
      const raw=await request.text();if(raw.length>1500)return answer({error:'too_large'},413,cors);
      let v;try{v=JSON.parse(raw)}catch{return answer({error:'bad_json'},400,cors)}
      if(!/^[0-9a-f-]{36}$/i.test(v?.quote_id||'')||
         !['email','signed_document','client_portal'].includes(v?.channel)||
         typeof v?.reference!=='string'||v.reference.trim().length<8||v.reference.length>190)
         return answer({error:'acceptance_evidence_required'},400,cors);
      const rows=await sql('SELECT agencia.register_client_acceptance($1::uuid,$2::text,$3::text,$4::text) AS recorded',
        [v.quote_id,user,v.channel,v.reference.trim()]);
      return rows[0]?.recorded === true||rows[0]?.recorded === 't'
        ?answer({ok:true,lead_status:'aprobado',recorded_by_owner:true},200,cors)
        :answer({error:'not_eligible_or_already_accepted'},409,cors);
    }
    // This creates only a local draft, NEVER a payment or a provider request.
    if(request.method==='POST'&&url.pathname==='/api/admin/payment/prepare'){
      const txt=await request.text();
      if(txt.length>1200)return answer({error:'too_large'},413,cors);
      let payload;try{payload=JSON.parse(txt)}catch{return answer({error:'bad_json'},400,cors)}
      const quoteId=payload?.quote_id,provider=payload?.provider;
      if(typeof quoteId!=='string'||!/^[0-9a-f-]{36}$/i.test(quoteId)
         ||!['arq_ach','arq_sepa','mercadopago_ar'].includes(provider))
         return answer({error:'invalid_request'},400,cors);
      const rows=await sql(`WITH ready AS (
        SELECT q.id,q.lead_id,q.quote_currency,q.quote_amount_minor
        FROM agencia.quote_drafts q JOIN agencia.leads l ON l.id=q.lead_id
        WHERE q.id=$1::uuid AND q.stage='enviado' AND q.sent_at IS NOT NULL AND q.quote_amount_minor>0
          AND q.quote_currency=CASE $2 WHEN 'arq_ach' THEN 'USD' WHEN 'arq_sepa' THEN 'EUR' ELSE 'ARS' END
          AND l.source='neon-web' AND l.status='aprobado'
          AND EXISTS(SELECT 1 FROM agencia.client_acceptances acc WHERE acc.quote_id=q.id AND acc.lead_id=q.lead_id AND acc.quote_currency=q.quote_currency AND acc.quote_amount_minor=q.quote_amount_minor)
          AND length(coalesce(q.scope_json->>'alcance_acordado',''))>=25
          AND length(coalesce(q.scope_json->>'entregables',''))>=20
          AND length(coalesce(q.scope_json->>'exclusiones',''))>=10
      ), ins AS (
        INSERT INTO agencia.payment_intents(lead_id,quote_id,provider,currency,amount_minor,state)
        SELECT lead_id,id,$2,quote_currency,quote_amount_minor,'draft' FROM ready WHERE true
        ON CONFLICT DO NOTHING
        RETURNING id,lead_id,provider,currency,amount_minor,state
      ), audit AS (
        INSERT INTO agencia.events(lead_id,event_type,actor,data)
        SELECT lead_id,'payment_draft_prepared',$3,jsonb_build_object('method',provider,'currency',currency,'amount_minor',amount_minor,'external_request_sent',false)
        FROM ins RETURNING id
      )
      SELECT id::text,provider,currency,amount_minor::text,state FROM ins`,[quoteId,provider,user]);
      return rows.length ? answer({ok:true,draft:rows[0],external_charge:false},201,cors)
                         : answer({error:'quote_or_payment_state_conflict'},409,cors);
    }
    // Read-only owner preflight. Does not send code, client PII or API keys to GitHub.
    // Even a clean DB preflight CANNOT authorize dispatch: independent repo privacy,
    // payment evidence, spending quota, and a restricted private runner must be checked.
    if(request.method==='GET'&&url.pathname==='/api/admin/work-orders/preflight'){
      const orderId=url.searchParams.get('order_id')||'';
      if(!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(orderId))
        return answer({error:'invalid_work_order_id'},400,cors);
      const rows=await sql('SELECT agencia.get_dispatch_readiness($1::uuid,$2::text) AS review',[orderId,user]);
      let review=rows[0]?.review;
      if(typeof review==='string'){try{review=JSON.parse(review)}catch{return answer({error:'invalid_review'},503,cors)}}
      if(review?.ok!==true)
        return answer({error:review?.code||'not_available'},review?.code==='order_not_found'?404:403,cors);
      return answer({ok:true,review,execution_authorized:false,dispatched:false},200,cors);
    }
    if(request.method==='GET'&&url.pathname==='/api/admin/work-spec'){
      const id=url.searchParams.get('quote_id')||'';
      if(!/^[0-9a-f-]{36}$/i.test(id))return answer({error:'invalid_quote_id'},400,cors);
      const row=await sql('SELECT agencia.build_work_spec($1::uuid) AS spec',[id]);
      let spec=row[0]?.spec;
      if(typeof spec==='string'){try{spec=JSON.parse(spec)}catch{return answer({error:'invalid_spec'},503,cors)}}
      if(!spec)return answer({error:'accepted_quote_required'},409,cors);
      return answer({ok:true,spec,execution_authorized:false},200,cors);
    }
    if(request.method==='POST'&&url.pathname==='/api/admin/work-orders/prepare'){
      const raw=await request.text();
      if(raw.length>800)return answer({error:'too_large'},413,cors);
      let v;try{v=JSON.parse(raw)}catch{return answer({error:'bad_json'},400,cors)}
      if(!/^[0-9a-f-]{36}$/i.test(v?.quote_id||'')||v?.confirm_blocked!==true)
        return answer({error:'owner_confirmation_required'},400,cors);
      const result=await sql('SELECT agencia.prepare_paid_work_order($1::uuid,$2::text) AS order_id',[v.quote_id,user]);
      return result[0]?.order_id
        ?answer({ok:true,order_id:result[0].order_id,execution_authorized:false,status:'blocked'},201,cors)
        :answer({error:'already_prepared_or_not_eligible'},409,cors);
    }
    return answer({error:'not_found'},404,cors);
  }catch(e){console.error('admin_error',e?.name||'unknown');return answer({error:'backend_unavailable'},503,cors)}
 }
};
