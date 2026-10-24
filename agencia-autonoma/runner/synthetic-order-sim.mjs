/**
 * Deterministic simulation of a whole software-agency order; NOT real fulfillment.
 * All clients, contract acceptance and payment acknowledgments are fictitious.
 * This file NEVER connects to a database, Claude, GitHub, banks or customers.
 */
import {createHash} from 'node:crypto';
import {mkdir,writeFile,readFile,readdir,lstat} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {buildSyntheticFiles,qaHtml} from './build-preview.mjs';

const sha=s=>createHash('sha256').update(s).digest('hex');
const names=['README.md','index.html','manifest.json','qa-report.json','order-review.json','bundle-hashes.json'];
const phases=Object.freeze([
  'intake_fixture','quote_review_fixture','fictional_acceptance',
  'payment_scenario_mock','owner_approval_mock',
  'deterministic_build','qa_checked','owner_delivery_review',
  'demo_packet_complete'
]);
export function assessSyntheticOrder(input){
 const blocks=[];
 if(!input||typeof input!=='object'||Array.isArray(input))
   return {ok:false,blockers:['invalid_scenario'],real_execution_allowed:false};
 if(input.kind!=='fictional_test_order_v1')blocks.push('not_a_fictional_fixture');
 if(input.real_customer===true||input.real_bank_transaction===true)blocks.push('real_orders_not_permitted');
 if(input.quote_accepted_in_fixture!==true)blocks.push('mock_acceptance_missing');
 if(input.payment_only_simulated!==true)blocks.push('mock_payment_flag_missing');
 if(input.owner_review_simulated!==true)blocks.push('mock_owner_review_missing');
 if(input.estimated_ai_cost_usd_cents!==0)blocks.push('nonzero_budget');
 if(input.private_repo_verified===true)blocks.push('cannot_claim_private_repo_attestation');
 if(input.claude_executed_for_order===true)blocks.push('cannot_claim_ai_job_completed');
 return {ok:blocks.length===0,blockers:blocks,real_execution_allowed:false,
  real_delivery_allowed:false,real_payment_verified:false};
}
export function exampleOrder(){
 return {kind:'fictional_test_order_v1',real_customer:false,
  real_bank_transaction:false,quote_accepted_in_fixture:true,
  payment_only_simulated:true,owner_review_simulated:true,
  estimated_ai_cost_usd_cents:0,private_repo_verified:false,
  claude_executed_for_order:false};
}
export function makeSyntheticOrderPacket(input=exampleOrder()){
 const assessment=assessSyntheticOrder(input);
 if(!assessment.ok)throw Error('Fictional order blocked: '+assessment.blockers.join(','));
 const files=buildSyntheticFiles(),html=files['index.html'];
 const checks=qaHtml(html);
 if(!checks.passed||Object.values(checks.checks).some(x=>x!==true))
   throw Error('Static QA not passed');
 const review={
  kind:'fictional_order_review_v1',
  fictional:true,real_client:false,real_bank_payment_verified:false,
  claude_code_executed_for_this_order:false,
  former_cli_smoke_test_is_not_this_order:true,
  actual_private_repo_verified:false,
  approved_for_customer_delivery:false,published:false,
  quote_acceptance_kind:'synthetic_fixture_not_contract',
  payment_evidence_kind:'synthetic_fixture_not_bank_settlement',
  manual_approval_kind:'synthetic_fixture_not_real_owner_consent',
  path:phases,simulated_ai_cost_usd_cents:0,
  quality:{passed:true,checks:Object.keys(checks.checks).length},
  required_before_real_work:['verified_client_identity','signed_quote','independent_paid_invoice_or_receipt',
    'approved_owner_login','verified_private_repository','live_nonbillable_model_quota',
    'owner_execution_authorization','actual_claude_code_run','independent_QA',
    'owner_delivery_approval'],
  final_state:'DEMO_ONLY_NOT_A_COMMERCIAL_DELIVERY'
 };
 files['order-review.json']=JSON.stringify(review,null,2)+'\n';
 files['README.md']+='\nFULL MOCK ORDER — acceptance, payment and owner review are simulated.\n'+
   'This packet cannot be delivered, used for billing, or advertised as customer work.\n'+
   'A previous real Claude Code smoke test does NOT mean Claude executed this mock order.\n';
 // Recalculate README SHA in the original preview manifest, which is its own integrity contract.
 const originalManifest=JSON.parse(files['manifest.json']);
 originalManifest.sha256_readme=sha(files['README.md']);
 files['manifest.json']=JSON.stringify(originalManifest,null,2)+'\n';
 const hashes=Object.fromEntries(Object.entries(files).map(([name,body])=>[name,sha(body)]));
 files['bundle-hashes.json']=JSON.stringify({
  kind:'synthetic_bundle_integrity_v1',
  file_hashes:hashes,
  note:'Digests detect accidental edits, not a forged or re-signed bundle. No trusted signature.'
 },null,2)+'\n';
 return files;
}
export async function exportSyntheticOrder(directory){
 if(typeof directory!=='string'||!directory.startsWith('/')||directory.includes('\0'))
   throw Error('An absolute new output directory is required');
 const target=resolve(directory);
 await mkdir(target,{recursive:false,mode:0o700});
 const files=makeSyntheticOrderPacket();
 for(const [name,content] of Object.entries(files))
   await writeFile(join(target,name),content,{flag:'wx',mode:0o600});
 return verifySyntheticOrder(target);
}
export async function verifySyntheticOrder(directory){
 if(typeof directory!=='string'||!directory.startsWith('/')||directory.includes('\0'))
   throw Error('Absolute path required');
 const target=resolve(directory),actual=(await readdir(target)).sort();
 if(JSON.stringify(actual)!==JSON.stringify([...names].sort()))
   throw Error('Unexpected or missing files');
 const files={};
 for(const name of names){
   if(!(await lstat(join(target,name))).isFile())throw Error('Non-regular file');
   files[name]=await readFile(join(target,name),'utf8');
 }
 const metadata=JSON.parse(files['bundle-hashes.json']);
 const review=JSON.parse(files['order-review.json']);
 const manifest=JSON.parse(files['manifest.json']);
 const qaReport=JSON.parse(files['qa-report.json']);
 const qa=qaHtml(files['index.html']);
 if(metadata.kind!=='synthetic_bundle_integrity_v1'||
   JSON.stringify(Object.keys(metadata.file_hashes||{}).sort())!==JSON.stringify(names.filter(x=>x!=='bundle-hashes.json').sort()))
   throw Error('Bundle file-list mismatch');
 for(const [name,digest] of Object.entries(metadata.file_hashes))
   if(sha(files[name])!==digest)throw Error('Tampering detected: '+name);
 if(review.kind!=='fictional_order_review_v1'||!review.fictional||
   review.real_client!==false||review.real_bank_payment_verified!==false||
   review.approved_for_customer_delivery!==false||review.published!==false||
   review.claude_code_executed_for_this_order!==false||
   review.final_state!=='DEMO_ONLY_NOT_A_COMMERCIAL_DELIVERY'||
   review.path.join('|')!==phases.join('|')||
   review.quality.checks!==15||qa.passed!==true||
   qaReport.passed!==true||
   JSON.stringify(qa.checks)!==JSON.stringify(qaReport.checks)||
   manifest.sha256_html!==sha(files['index.html'])||
   manifest.sha256_qa_report!==sha(files['qa-report.json'])||
   manifest.sha256_readme!==sha(files['README.md'])||
   manifest.bank_payment_verified!==false||
   manifest.claude_executed!==false||
   manifest.can_be_delivered_to_client!==false)
   throw Error('Unsafe or inconsistent synthetic artifact');
 return {ok:true,kind:review.kind,stages:phases.length,qa_checks:15,
  fictional:true,real_bank_payment:false,customer_delivery_allowed:false,
  claude_executed_for_this_order:false,files:actual};
}
if(process.argv[1]&&import.meta.url===new URL('file://'+resolve(process.argv[1])).href){
 try {
  const args=process.argv.slice(2);
  const result=args.length===3&&args[0]==='--demo'&&args[1]==='--output'
   ?await exportSyntheticOrder(args[2]):
   args.length===2&&args[0]==='--verify'
   ?await verifySyntheticOrder(args[1]):
   (()=>{throw Error('Usage: --demo --output /absolute/new/dir OR --verify /absolute/dir')})();
  process.stdout.write(JSON.stringify(result)+'\n');
 }catch(e){process.stderr.write('Synthetic agency flow: '+(e?.message||'error')+'\n');process.exitCode=1}
}
