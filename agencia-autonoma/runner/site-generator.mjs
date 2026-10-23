/**
 * Deterministic STATIC SITE PREVIEW, not Claude Code or a client deliverable.
 * No network, no credentials, no tracking and no third-party libraries.
 * Converts an explicitly gated agency handoff into one self-contained HTML file.
 */
export function generateStaticPreview(handoff){
 if(!handoff||handoff.ok!==true||handoff.may_start!==false||!handoff.requires_owner_action)
  throw new Error('Owner-reviewed work specification required');
 const brief=handoff.brief;
 if(!brief||brief.version!=='agency_handoff_v1'||brief.boundaries?.automerge!==false||
    brief.boundaries?.secrets!==false||brief.boundaries?.production_deploy!==false||
    brief.boundaries?.customer_text_is_instructions!==false)
  throw new Error('Insecure or malformed handoff');
 const data=brief.untrusted_customer_data||{};
 for(const k of ['scope','deliverables','exclusions']){
   if(typeof data[k]!=='string'||!data[k].trim()||data[k].length>1800)
    throw new Error('Incomplete content: '+k);
 }
 const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const cut=(v,n)=>v.trim().slice(0,n);
 const scope=esc(cut(data.scope,750)),deliverables=esc(cut(data.deliverables,650));
 const exclusions=esc(cut(data.exclusions,450));
 const websiteTitle='A clear, practical website';
 const value='Design that helps visitors understand your service';
 const html=`<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<meta name="description" content="Private, unpublished concept preview for review.">
<title>${websiteTitle} | Internal Concept</title>
<style>
:root{color-scheme:light;--bg:#f4f7f5;--ink:#183327;--muted:#5d6c64;--accent:#27744f;--line:#cadbd0}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 system-ui,sans-serif}
header{background:#fff;border-bottom:1px solid var(--line);padding:1rem clamp(1rem,5vw,5rem);display:flex;justify-content:space-between;align-items:center;gap:1rem}
header strong{font-size:1.2rem;letter-spacing:-.035em}header span{color:var(--muted);font-size:.82rem}
main{max-width:1020px;margin:auto;padding:clamp(1.1rem,4vw,4rem)}h1{font-size:clamp(2.7rem,9vw,5.5rem);line-height:1.05;letter-spacing:-.065em;margin:0 0 1.7rem}h2{font-size:clamp(1.6rem,4vw,2.4rem);letter-spacing:-.04em;line-height:1.2}
.hero{padding:clamp(3rem,9vw,7rem) 0 3rem}.eyebrow{text-transform:uppercase;font-size:.75rem;letter-spacing:.12em;font-weight:750;color:var(--accent)}.lead{font-size:clamp(1.1rem,2.2vw,1.4rem);color:var(--muted);max-width:600px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:1.25rem;margin:4rem 0}.panel{border:1px solid var(--line);padding:clamp(1.4rem,3vw,2.5rem);border-radius:12px;background:white;overflow-wrap:anywhere}
.panel p{color:var(--muted)}.full{grid-column:1/-1}.button{display:inline-block;background:var(--accent);color:white;text-decoration:none;padding:.8rem 1.2rem;border-radius:7px;font-weight:700}
.notice{background:#e2eee5;padding:1rem 1.5rem;border-radius:8px;font-size:.82rem;color:#234935}footer{border-top:1px solid var(--line);padding:2rem;text-align:center;font-size:.8rem;color:var(--muted)}
@media(max-width:640px){.grid{grid-template-columns:1fr}.hero{padding-top:4rem}header{align-items:flex-start;flex-direction:column}}
:focus-visible{outline:3px solid var(--accent);outline-offset:3px}
</style></head><body>
<header><strong>Concept · Studio</strong><span>Responsive single-page prototype</span></header>
<main><section class="hero" aria-labelledby="headline">
<p class="eyebrow">Private design concept</p><h1 id="headline">${websiteTitle}.</h1>
<p class="lead">${value}. Simple structure, readable content and a clean mobile experience.</p>
<a class="button" href="#project">Explore concept ↓</a></section>
<div class="grid" id="project">
<section class="panel"><p class="eyebrow">01 · Scope</p><h2>What this solves</h2><p>${scope}</p></section>
<section class="panel"><p class="eyebrow">02 · Deliverables</p><h2>What is included</h2><p>${deliverables}</p></section>
<section class="panel full"><p class="eyebrow">03 · Boundaries</p><h2>Clear expectations</h2><p>${exclusions}</p></section>
</div><p class="notice" role="note">INTERNAL PREVIEW ONLY — not a client launch, not acceptance, not proof of completed work. Replace placeholder branding after owner review.</p></main>
<footer>Autónoma Dev · Generated offline for quality review</footer></body></html>`;
 if(html.length>16000)throw new Error('Preview output too large');
 return {format:'text/html',published:false,needs_approval:true,template:'static-concept-v1',html};
}
