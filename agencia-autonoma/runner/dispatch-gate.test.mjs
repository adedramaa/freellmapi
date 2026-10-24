import test from 'node:test';
import assert from 'node:assert/strict';
import {assessDispatchReadiness} from './dispatch-gate.mjs';
const now='2026-10-24T02:15:00Z';
const pass=()=>({
 checkedAt:now,
 review:{
  ok:true,order_id:'71111111-1111-4111-8111-111111111111',status:'plan_ready',
  eligible_for_external_repo_check:true,may_dispatch:false,blockers:[],
  payment_method_independently_reconciled:true,repo_full_name:'adedramaa/client-test-private',
  max_cost_usd_cents:0,approved_at:'2026-10-24T02:00:00Z',
  expires_at:'2026-10-24T03:00:00Z'
 },
 githubRepository:{full_name:'adedramaa/client-test-private',private:true,visibility:'private',
  archived:false,disabled:false,fork:false,owner:{login:'adedramaa'},
  permissions:{push:true}},
 event:{name:'workflow_dispatch',actor:'adedramaa',
  repository:'adedramaa/client-test-private',ref:'refs/heads/main'},
 billingEvidence:{source:'verified_live_provider',billing_enabled:false,
  expected_cost_usd_cents:0,checked_at:'2026-10-24T02:14:00Z'}
});
test('fully verified synthetic inputs pass all prechecks but never autonomously dispatch',()=>{
 const x=assessDispatchReadiness(pass());assert.equal(x.eligible,true);
 assert.deepEqual(x.errors,[]);assert.equal(x.auto_dispatch,false);
});
for(const [name,change,expected] of [
 ['public repo',v=>{v.githubRepository.private=false;v.githubRepository.visibility='public'},'repo_not_privately_verified'],
 ['wrong repository',v=>{v.githubRepository.full_name='adedramaa/another'},'repo_not_privately_verified'],
 ['unapproved quote',v=>{v.review.blockers=['client_acceptance_missing']},'neon_approval_missing'],
 ['unreconciled payment',v=>{v.review.payment_method_independently_reconciled=false},'payment_not_independently_reconciled'],
 ['unapproved CI actor',v=>{v.event.actor='other-user'},'owner_or_event_not_authenticated'],
 ['nonzero budget',v=>{v.review.max_cost_usd_cents=100},'budget_not_zero'],
 ['expired owner grant',v=>{v.review.expires_at='2026-10-24T02:14:00Z'},'authorization_expired_or_invalid'],
 ['invalid owner grant',v=>{v.review.approved_at='2026-10-25T02:14:00Z'},'authorization_expired_or_invalid'],
 ['billable API',v=>{v.billingEvidence.billing_enabled=true},'unverified_free_provider'],
 ['stale provider check',v=>{v.billingEvidence.checked_at='2026-10-24T01:50:00Z'},'unverified_free_provider'],
 ['untrusted repository path',v=>{v.review.repo_full_name='../../secret'},'repo_not_configured']
]){
 test('fails closed: '+name,()=>{const sample=pass();change(sample);
  const res=assessDispatchReadiness(sample);
  assert.equal(res.eligible,false);assert.ok(res.errors.includes(expected));
  assert.equal(res.auto_dispatch,false);
 });
}
test('empty or inconsistent input never allows execution',()=>{
 for(const input of [null,{},[],{checkedAt:'invalid'},{checkedAt:now,review:{may_dispatch:true}}])
  assert.equal(assessDispatchReadiness(input).auto_dispatch,false);
});
