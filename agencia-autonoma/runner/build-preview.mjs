/**
 * Offline synthetic-demo export. Never receives real customer records and never
 * calls an AI model, GitHub, a payment service or the agency database.
 *
 * Examples:
 *   node build-preview.mjs --demo --output /tmp/agency-synthetic-demo
 *   node build-preview.mjs --verify /tmp/agency-synthetic-demo
 */
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { createHash } from 'node:crypto';
import { compileHandoff, REQUIRED_SKILLS } from './compile-handoff.mjs';
import { generateStaticPreview } from './site-generator.mjs';

const sha256 = value => createHash('sha256').update(value).digest('hex');
const EXAMPLE = Object.freeze({
  version: 'work_spec_v1',
  quote_id: 'b2be620a-e49e-4072-afbe-a27bb6b63410',
  service: 'web', currency: 'USD', amount_minor: '25000',
  scope: 'Create a fictional bakery landing page with clear sections and an accessible mobile layout.',
  deliverables: 'One static HTML page, responsive CSS and documented review checks.',
  exclusions: 'No real bakery, payments, clients, API subscriptions, hosting or data collection.',
  delivery_days: '5', included_revisions: '1',
  payment_verified: true, // Synthetic test fixture only. Never bank confirmation.
  execution_authorized: false, customer_text_untrusted: true,
  owner_review_required: true, execution_environment: 'private_restricted_repository',
  skills_required: [...REQUIRED_SKILLS],
  qa_required: ['build','tests','security','mobile','documentation','privacy']
});

export function qaHtml(html) {
  const checks = {
    doctype: /^<!doctype html>/i.test(html),
    responsive: /<meta name="viewport"[^>]*width=device-width/i.test(html),
    indexed_disabled: /name="robots"[^>]*noindex,nofollow/i.test(html),
    no_script: !/<script\b/i.test(html) && !/javascript\s*:/i.test(html),
    no_network_dependencies: !/https?:\/\//i.test(html) && !/@import\b/i.test(html),
    no_forms_or_passwords: !/<form\b|<input\b|type\s*=\s*["']password/i.test(html),
    semantic_markup: /<main\b/i.test(html) && /<h1\b/i.test(html) && /<footer\b/i.test(html),
    accessible_focus: /:focus-visible/.test(html),
    mobile_css: /@media\s*\(max-width:\s*640px\)/i.test(html),
    reasonable_size: html.length > 800 && html.length < 120000,
    explicitly_fictional: /INTERNAL PREVIEW ONLY|PUBLIC FICTIONAL EXAMPLE/.test(html)
  };
  return {passed: Object.values(checks).every(Boolean), checks};
}
export function buildSyntheticFiles() {
  const handoff = compileHandoff(EXAMPLE);
  if (!handoff.ok || handoff.may_start !== false) throw new Error('Untrusted demo handoff');
  const html = generateStaticPreview(handoff).html;
  const qa = qaHtml(html);
  if (!qa.passed) throw new Error('Static quality gate failed');
  const manifest = {
    kind: 'synthetic_static_preview_v1', fictional: true, actual_customer: false,
    bank_payment_verified: false, claude_executed: false, external_provider_used: false,
    published: false, can_be_delivered_to_client: false, owner_review_required: true,
    sha256_html: sha256(html), quality_checks_passed: Object.keys(qa.checks).length,
    tools: ['offline deterministic code generator'],
    limitations: ['This is a toy brochure page, not a completed client project.',
      'No authentication, backend, live payments or model execution is demonstrated.']
  };
  const readme = '# Autónoma Dev — fictional demo artifact\n\n' +
    'This directory contains a synthetic concept, not a customer deliverable.\n\n' +
    'The placeholder payment flag in test data is NOT evidence of any transaction.\n' +
    'Generated with a deterministic, offline script. Claude Code was NOT invoked.\n' +
    'Do not deploy or hand over as a commercial job without separate approval.\n';
  return {
    'index.html': html,
    'qa-report.json': JSON.stringify(qa,null,2)+'\n',
    'manifest.json': JSON.stringify(manifest,null,2)+'\n',
    'README.md': readme
  };
}
export async function exportDemo(directory) {
  if(typeof directory !== 'string' || !directory.startsWith('/') || directory.includes('\0'))
    throw new Error('Use an absolute destination path');
  const target = resolve(directory);
  // Exclusive creation: never overwrite existing files or another project.
  await mkdir(target, {recursive:false,mode:0o700});
  const files=buildSyntheticFiles();
  for(const [name,content] of Object.entries(files))
    await writeFile(join(target,name),content,{flag:'wx',mode:0o600});
  return verifyDemo(target);
}
export async function verifyDemo(directory) {
  const target = resolve(directory);
  const html = await readFile(join(target,'index.html'),'utf8');
  const manifest = JSON.parse(await readFile(join(target,'manifest.json'),'utf8'));
  const qa = qaHtml(html);
  const ok = manifest.kind==='synthetic_static_preview_v1' &&
    manifest.fictional===true && manifest.actual_customer===false &&
    manifest.claude_executed===false && manifest.published===false &&
    manifest.bank_payment_verified===false &&
    qa.passed && manifest.sha256_html===sha256(html);
  if(!ok)throw new Error('Artifact validation failed (tampered or unsafe)');
  return {ok:true, directory:target, sha256_html:sha256(html), checks:Object.keys(qa.checks).length,
    files:['index.html','qa-report.json','manifest.json','README.md']};
}
if(process.argv[1] && import.meta.url===new URL('file://'+resolve(process.argv[1])).href){
  const args=process.argv.slice(2);
  try{
    let report;
    if(args.length===3 && args[0]==='--demo' && args[1]==='--output')
      report=await exportDemo(args[2]);
    else if(args.length===2 && args[0]==='--verify')
      report=await verifyDemo(args[1]);
    else throw new Error('Usage: --demo --output /absolute/new/dir OR --verify /absolute/dir');
    process.stdout.write(JSON.stringify(report)+'\n');
  }catch(e){
    process.stderr.write('Agency artifact gate: '+(e?.message||'error')+'\n');
    process.exitCode=1;
  }
}
