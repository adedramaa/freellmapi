/** Scheduled uptime and lead-queue snapshot. No outbound email, no client PII. */
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

const PAGE='https://autonoma-dev-agencia-v2.onrender.com/';
const HEALTH='https://br-falling-night-b57zpkln-agencialeads.compute.c-7.us-east-2.aws.neon.tech/health';
async function ping(url,needle){
 try {
  const result=await fetch(url,{method:'GET',signal:AbortSignal.timeout(10000),headers:{'Cache-Control':'no-cache'}});
  if(!result.ok)return false;
  const body=(await result.text()).slice(0,2500);
  return body.includes(needle);
 }catch{return false}
}
export default {
 async fetch(req){
  if(req.method!=='POST'||!req.headers.get('x-neon-trigger-invocation-id'))
   return new Response(JSON.stringify({error:'not_scheduled'}),{status:403,headers:{'Content-Type':'application/json','Cache-Control':'no-store'}});
  let scheduled;
  try{
    const body=await req.json();
    scheduled=body?.data?.scheduled_at;
    if(typeof scheduled!=='string'||!/^\d{4}-\d{2}-\d{2}T/.test(scheduled))throw new Error('missing_schedule');
    const d=Date.parse(scheduled);
    if(!Number.isFinite(d)||Math.abs(Date.now()-d)>7200000)throw new Error('stale_schedule');
  }catch{return new Response(JSON.stringify({error:'bad_schedule'}),{status:400,headers:{'Content-Type':'application/json'}})}
  const slot=new Date(scheduled).toISOString().slice(0,13)+':00:00.000Z';
  const [web,api]=await Promise.all([ping(PAGE,'Autónoma Dev'),ping(HEALTH,'"database":"verified"')]);
  // Avoid retaining hashed email anti-duplicate locks for longer than needed.
  try{await sql("DELETE FROM agencia.lead_submission_locks WHERE last_submitted_at < now()-interval '24 hours'")}catch(e){console.error('lead_lock_cleanup',e?.name||'unknown')}
  try{
    const rows=await sql(`
       WITH counts AS (
         SELECT count(*) FILTER(WHERE source='neon-web')::integer AS total,
           count(*) FILTER(WHERE source='neon-web' AND status='nuevo')::integer AS pending
         FROM agencia.leads
       ), inserted AS (
         INSERT INTO agencia.monitor_snapshots(slot,website_ok,backend_ok,pending_leads,total_leads,error_flags)
         SELECT $1::timestamptz,$2::boolean,$3::boolean,counts.pending,counts.total,
           jsonb_build_array(CASE WHEN $2::boolean THEN 'website_ok' ELSE 'website_unavailable' END,
                             CASE WHEN $3::boolean THEN 'api_ok' ELSE 'api_unavailable' END)
         FROM counts ON CONFLICT(slot) DO UPDATE SET checked_at=now(),website_ok=EXCLUDED.website_ok,backend_ok=EXCLUDED.backend_ok,pending_leads=EXCLUDED.pending_leads,total_leads=EXCLUDED.total_leads,error_flags=EXCLUDED.error_flags
         RETURNING slot
       ) SELECT counts.pending,counts.total,(SELECT count(*) FROM inserted)::integer AS inserted FROM counts
    `,[slot,web,api]);
    const r=rows[0]||{};
    return new Response(JSON.stringify({ok:true,recorded:Number(r.inserted)===1,web,api,pending:Number(r.pending||0)}),{headers:{'Content-Type':'application/json','Cache-Control':'no-store'}});
  }catch(e){console.error('monitor_failure',e?.name||'unknown');return new Response(JSON.stringify({error:'monitor_unavailable'}),{status:503,headers:{'Content-Type':'application/json'}})}
 }
};