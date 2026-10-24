import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,writeFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {assessSyntheticOrder,exampleOrder,makeSyntheticOrderPacket,
 exportSyntheticOrder,verifySyntheticOrder} from './synthetic-order-sim.mjs';
test('requires mock acceptance, payment and review yet NEVER grants real authorization',()=>{
 const result=assessSyntheticOrder(exampleOrder());
 assert.equal(result.ok,true);
 assert.equal(result.real_execution_allowed,false);
 assert.equal(result.real_delivery_allowed,false);
 assert.equal(result.real_payment_verified,false);
});
for(const [name,mutate,block] of [
 ['real customer',x=>x.real_customer=true,'real_orders_not_permitted'],
 ['real payment',x=>x.real_bank_transaction=true,'real_orders_not_permitted'],
 ['missing acceptance',x=>x.quote_accepted_in_fixture=false,'mock_acceptance_missing'],
 ['missing payment fixture',x=>x.payment_only_simulated=false,'mock_payment_flag_missing'],
 ['missing owner approval',x=>x.owner_review_simulated=false,'mock_owner_review_missing'],
 ['paid model',x=>x.estimated_ai_cost_usd_cents=1,'nonzero_budget'],
 ['fake private repo',x=>x.private_repo_verified=true,'cannot_claim_private_repo_attestation'],
 ['fake Claude delivery',x=>x.claude_executed_for_order=true,'cannot_claim_ai_job_completed']
]){
 test('blocks fake order transition: '+name,()=>{
  const x=exampleOrder();mutate(x);
  assert.equal(assessSyntheticOrder(x).ok,false);
  assert.ok(assessSyntheticOrder(x).blockers.includes(block));
  assert.throws(()=>makeSyntheticOrderPacket(x),/Fictional order blocked/);
 });
}
test('packet is purely synthetic and all evidence files are cross-consistent',()=>{
 const files=makeSyntheticOrderPacket(),review=JSON.parse(files['order-review.json']);
 assert.equal(Object.keys(files).length,6);
 assert.equal(review.path.length,9);
 assert.equal(review.approved_for_customer_delivery,false);
 assert.equal(review.real_bank_payment_verified,false);
 assert.equal(review.claude_code_executed_for_this_order,false);
 assert.equal(review.quality.checks,15);
});
test('writes exclusive read-only demonstration packet and validates every file',async()=>{
 const root=await mkdtemp(join(tmpdir(),'agency-flow-'));
 const dest=join(root,'fictional-order');
 try{
  const a=await exportSyntheticOrder(dest);
  assert.equal(a.ok,true);
  assert.equal(a.files.length,6);
  assert.equal(a.customer_delivery_allowed,false);
  const b=await verifySyntheticOrder(dest);
  assert.deepEqual(b,a);
  await assert.rejects(()=>exportSyntheticOrder(dest),/EEXIST/);
  const original=await readFile(join(dest,'order-review.json'),'utf8');
  await writeFile(join(dest,'order-review.json'),original.replace('"approved_for_customer_delivery": false','"approved_for_customer_delivery": true'));
  await assert.rejects(()=>verifySyntheticOrder(dest),/Tampering detected/);
  await writeFile(join(dest,'order-review.json'),original);
  const readme=await readFile(join(dest,'README.md'),'utf8');
  await writeFile(join(dest,'README.md'),readme+'fake proof');
  await assert.rejects(()=>verifySyntheticOrder(dest),/Tampering detected/);
 }finally{await rm(root,{recursive:true,force:true})}
});
test('cannot silently generate into a relative or pre-existing folder',async()=>{
 await assert.rejects(()=>exportSyntheticOrder('./anywhere'),/absolute new output/i);
});
