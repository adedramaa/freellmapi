/**
 * Pure, offline handoff compiler. Never invokes an AI API, shell, network or GitHub.
 * The database remains authoritative for payments, acceptance and administrator rights.
 * Output is a reviewable PROPOSAL, never approval to execute.
 */
export const REQUIRED_SKILLS=Object.freeze([
 'agencia-arquitecto','agencia-programador','agencia-qa','agencia-entregas'
]);
const CURRENCIES=new Set(['ARS','USD','EUR']);
const SERVICES=new Set(['web','automatizacion','aplicacion','mantenimiento','otro']);
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
function validText(value,max){return typeof value==='string'&&value.trim().length>=12&&value.length<=max}
function mayContainPrivateData(value){
 if(typeof value!=='string')return false;
 return /[\\w.+-]+@[\\w.-]+\\.[a-z]{2,}/i.test(value) ||
  /\\b(?:api[_\\s-]?key|auth[_\\s-]?token|password|contraseña|client[_\\s-]?secret)\\s*[:=]\\s*[^\\s,;]{4,}/i.test(value) ||
  /\\b(?:dni|cuit|passport|pasaporte|credit[_\\s-]?card|tarjeta)\\s*[:=#]?\\s*\\d{7,}/i.test(value);
}
export function assessHandoff(spec){
 const blockers=[];
 if(!spec||typeof spec!=='object'||Array.isArray(spec))return ['invalid_spec'];
 if(spec.version!=='work_spec_v1')blockers.push('invalid_version');
 if(!UUID.test(String(spec.quote_id||'')))blockers.push('invalid_quote_reference');
 if(!CURRENCIES.has(spec.currency)||!SERVICES.has(spec.service))blockers.push('invalid_quote_terms');
 if(!validText(spec.scope,1800))blockers.push('missing_scope');
 if(!validText(spec.deliverables,1400))blockers.push('missing_deliverables');
 if(!validText(spec.exclusions,900))blockers.push('missing_exclusions');
 if(!Number.isSafeInteger(Number(spec.amount_minor))||Number(spec.amount_minor)<=0)
  blockers.push('invalid_quote_amount');
 if(!Number.isInteger(Number(spec.delivery_days))||Number(spec.delivery_days)<1||Number(spec.delivery_days)>180)
  blockers.push('invalid_delivery_window');
 if(!Number.isInteger(Number(spec.included_revisions))||Number(spec.included_revisions)<0||Number(spec.included_revisions)>8)
  blockers.push('invalid_revision_count');
 if([spec.scope,spec.deliverables,spec.exclusions].some(mayContainPrivateData))
  blockers.push('possible_private_data_requires_redaction');
 if(spec.payment_verified!==true)blockers.push('unverified_payment');
 if(spec.customer_text_untrusted!==true)blockers.push('missing_prompt_injection_boundary');
 if(spec.execution_authorized!==false)blockers.push('unsafe_execution_flag');
 if(spec.owner_review_required!==true)blockers.push('owner_review_not_required');
 if(spec.execution_environment!=='private_restricted_repository')blockers.push('unisolated_repository');
 if(!Array.isArray(spec.skills_required)||REQUIRED_SKILLS.some(s=>!spec.skills_required.includes(s)))
  blockers.push('missing_required_skills');
 if(!Array.isArray(spec.qa_required)||['build','tests','security','mobile'].some(s=>!spec.qa_required.includes(s)))
  blockers.push('qa_not_defined');
 return blockers;
}
export function compileHandoff(spec){
 const blockers=assessHandoff(spec);
 if(blockers.length) return {ok:false,blockers,may_start:false};
 return {
  ok:true,may_start:false,requires_owner_action:true,
  brief:{
   version:'agency_handoff_v1',quote_id:spec.quote_id,
   currency:spec.currency,amount_minor:String(spec.amount_minor),
   project_type:spec.service,
   deadline_days:Number(spec.delivery_days),revisions:Number(spec.included_revisions),
   untrusted_customer_data:{scope:spec.scope,deliverables:spec.deliverables,exclusions:spec.exclusions},
   required_skills:[...REQUIRED_SKILLS],
   boundaries:{target:'private isolated client repository only',
    customer_text_is_instructions:false,external_network:false,
    secrets:false,automerge:false,production_deploy:false,
    approve_budget_manually:true,qa_independent:true,
    git_pull_request_required:true}
  }
 };
}
