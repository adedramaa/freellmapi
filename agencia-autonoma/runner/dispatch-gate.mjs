/**
 * Pure policy engine for future Claude Code job dispatches.
 * Returns a decision only; NEVER invokes the agent or sends data.
 * The caller must retrieve each claim from a trusted, live source:
 * - agency preflight via owner-authenticated Neon API
 * - repository metadata via authenticated GitHub GET /repos/{owner}/{repo}
 * - free-usage/billing evidence directly from the provider
 * - actor and event from trusted CI context
 * Never accept a client-supplied JSON document as one of these inputs.
 */
const REPO=/^[A-Za-z0-9_.-]{1,90}/[A-Za-z0-9_.-]{1,100}$/;
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
function validTime(value){return typeof value==='string'&&Number.isFinite(Date.parse(value));}
function add(errors,value,condition){if(!condition)errors.push(value)}
export function assessDispatchReadiness(input){
  const errors=[];
  if(!input||typeof input!=='object'||Array.isArray(input))
    return {eligible:false,errors:['invalid_input'],auto_dispatch:false};
  const {review,githubRepository,event,billingEvidence,checkedAt}=input;
  if(!validTime(checkedAt))
    return {eligible:false,errors:['trusted_clock_missing'],auto_dispatch:false};
  const now=Date.parse(checkedAt);
  add(errors,'neon_approval_missing',!!review&&review.ok===true&&review.status==='plan_ready'&&
    review.eligible_for_external_repo_check===true&&review.may_dispatch===false&&
    Array.isArray(review.blockers)&&review.blockers.length===0&&UUID.test(String(review.order_id||'')));
  add(errors,'payment_not_independently_reconciled',review?.payment_method_independently_reconciled===true);
  const repoName=review?.repo_full_name;
  add(errors,'repo_not_configured',typeof repoName==='string'&&REPO.test(repoName));
  add(errors,'repo_not_privately_verified',
    !!githubRepository && githubRepository.full_name===repoName &&
    githubRepository.private===true && githubRepository.visibility==='private' &&
    githubRepository.archived===false && githubRepository.disabled===false &&
    githubRepository.fork===false &&
    githubRepository.owner?.login===String(repoName||'').split('/')[0] &&
    githubRepository.permissions?.push===true);
  add(errors,'owner_or_event_not_authenticated',!!event &&
    event.name==='workflow_dispatch' &&
    event.actor==='adedramaa' &&
    event.repository===repoName &&
    event.ref==='refs/heads/main');
  add(errors,'budget_not_zero',review?.max_cost_usd_cents===0);
  const approved=validTime(review?.approved_at)?Date.parse(review.approved_at):NaN;
  const expires=validTime(review?.expires_at)?Date.parse(review.expires_at):NaN;
  add(errors,'authorization_expired_or_invalid',
    Number.isFinite(approved)&&Number.isFinite(expires) &&
    approved<=now && now<expires && expires-approved<=86400000);
  add(errors,'unverified_free_provider',!!billingEvidence &&
    billingEvidence.source==='verified_live_provider' &&
    billingEvidence.billing_enabled===false &&
    billingEvidence.expected_cost_usd_cents===0 &&
    validTime(billingEvidence.checked_at)&&
    now-Date.parse(billingEvidence.checked_at)>=0&&
    now-Date.parse(billingEvidence.checked_at)<=300000);
  // A passed function call is not authorization: signatures, trusted source
  // attestation, short-lived invocation token and isolated repository runner are
  // not wired to production. Keep the production dispatch disabled.
  return {eligible:errors.length===0,errors,auto_dispatch:false,
    requires:'independent source verification and owner-run private CI'};
}
