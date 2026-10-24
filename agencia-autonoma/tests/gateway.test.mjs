import test from 'node:test';
import assert from 'node:assert/strict';
import publicLead from '../neon/index.mjs';
import admin from '../neon/admin.mjs';

const WEB='https://autonoma-dev-agencia-v2.onrender.com';
const PUBLIC='https://test.local/api/lead';
const ADMIN='https://test.local/api/admin/leads';

function payload(overrides={}){
 return {
  name:'Demo No Data',email:'test-gateway@invalid.example',business:'Test only',
  service:'web',budget:'no_definido',details:'This is a synthetic no-network validation test, with more than 20 characters.',
  honey:'',consent:true,language:'en',country:'US',currency:'USD',global_budget:'unknown',...overrides
 };
}
async function post(data,origin=WEB){
 const r=new Request(PUBLIC,{method:'POST',headers:{Origin:origin,'Content-Type':'application/json'},body:JSON.stringify(data)});
 return publicLead.fetch(r);
}
test('rejects unauthorized origin even with valid input',async()=>{
 const r=await post(payload(),'https://malicious.example');assert.equal(r.status,403);
});
test('rejects missing consent before database access',async()=>{
 const r=await post(payload({consent:false}));assert.equal(r.status,400);
});
test('rejects invalid ISO country before database access',async()=>{
 const r=await post(payload({country:'USA'}));assert.equal(r.status,400);
});
test('rejects unsupported quote currency before database access',async()=>{
 const r=await post(payload({currency:'BTC'}));assert.equal(r.status,400);
});
test('rejects invalid international budget before database access',async()=>{
 const r=await post(payload({global_budget:'500k'}));assert.equal(r.status,400);
});
test('rejects local ARS with foreign budget tiers',async()=>{
 const r=await post(payload({country:'AR',currency:'ARS',global_budget:'500_1500'}));assert.equal(r.status,400);
});
test('rejects badly formatted request',async()=>{
 const r=await publicLead.fetch(new Request(PUBLIC,{method:'POST',headers:{Origin:WEB,'Content-Type':'application/json'},body:'INVALID'}));assert.equal(r.status,400);
});
test('rejects disallowed method',async()=>{
 const r=await publicLead.fetch(new Request(PUBLIC,{method:'GET',headers:{Origin:WEB}}));assert.equal(r.status,404);
});
test('accepts CORS preflight for public intake',async()=>{
 const r=await publicLead.fetch(new Request(PUBLIC,{method:'OPTIONS',headers:{Origin:WEB}}));assert.equal(r.status,204);
});
test('rejects unauthenticated admin even from own origin',async()=>{
 const r=await admin.fetch(new Request(ADMIN,{method:'GET',headers:{Origin:WEB}}));assert.equal(r.status,401);
});
test('rejects token-looking input with bad signature',async()=>{
 const r=await admin.fetch(new Request(ADMIN,{method:'GET',headers:{Origin:WEB,Authorization:'Bearer garbage'}}));assert.equal(r.status,401);
});
test('rejects admin cross-origin requests before auth',async()=>{
 const r=await admin.fetch(new Request(ADMIN,{method:'GET',headers:{Origin:'https://evil.example'}}));assert.equal(r.status,403);
});
test('accepts admin CORS preflight only from production domain',async()=>{
 const ok=await admin.fetch(new Request(ADMIN,{method:'OPTIONS',headers:{Origin:WEB}}));
 const bad=await admin.fetch(new Request(ADMIN,{method:'OPTIONS',headers:{Origin:'https://evil.example'}}));
 assert.equal(ok.status,204);assert.equal(bad.status,403);
});


test('refuses oversize JSON before parsing (12 KiB memory gate)',async()=>{
 const r=await post(payload({details:'X'.repeat(20_000)}));
 assert.equal(r.status,413);
 const body=await r.json();assert.equal(body.error,'too_large');
});
test('refuses large declared Content-Length without reading body',async()=>{
 const r=await publicLead.fetch(new Request(PUBLIC,{method:'POST',
  headers:{Origin:WEB,'Content-Type':'application/json','Content-Length':'99000'},
  body:JSON.stringify(payload())}));
 assert.equal(r.status,413);
});
test('rejects multibyte Unicode payload by bytes, not JS characters',async()=>{
 const r=await post(payload({details:'😀'.repeat(3500)}));
 assert.equal(r.status,413);
});
test('truncated or malformed request remains a 400, no database call',async()=>{
 const r=await publicLead.fetch(new Request(PUBLIC,{method:'POST',
  headers:{Origin:WEB,'Content-Type':'application/json'},body:'{"name":'}));
 assert.equal(r.status,400);
});


test('admin requires verified and unbanned user even when allowlisted',async()=>{
 const {readFile}=await import('node:fs/promises');
 const source=await readFile(new URL('../neon/admin.mjs',import.meta.url),'utf8');
 assert.match(source,/u\."emailVerified"=true/);
 assert.match(source,/COALESCE\(u\."banned",false\)=false/);
 assert.match(source,/a\.active=true AND a\.approved_at IS NOT NULL/);
});
test('Android owner email OTP must use managed Neon endpoint and not self-approve',async()=>{
 const {readFile}=await import('node:fs/promises');
 const source=await readFile(new URL('../site/admin/index.html',import.meta.url),'utf8');
 assert.match(source,/email-otp\/send-verification-otp/);
 assert.match(source,/email-otp\/verify-email/);
 assert.match(source,/autocomplete="one-time-code"/);
 assert.match(source,/credentials:'include'/);
 assert.match(source,/await refreshOwnerAccess\(\)/);
 assert.doesNotMatch(source,/UPDATE\s+agencia\.admin_users/i);
});
