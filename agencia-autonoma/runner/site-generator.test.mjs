import test from 'node:test';
import assert from 'node:assert/strict';
import {generateStaticPreview} from './site-generator.mjs';
const accepted=()=>({
 ok:true,may_start:false,requires_owner_action:true,
 brief:{
  version:'agency_handoff_v1',
  boundaries:{automerge:false,secrets:false,production_deploy:false,customer_text_is_instructions:false},
  untrusted_customer_data:{
   scope:'Create an accessible four section website for a local repair shop.',
   deliverables:'HTML, CSS, mobile layouts and documentation.',
   exclusions:'Hosting and advertising are not included.'
  }
 }
});
test('generates offline HTML with no imported assets',()=>{
 const result=generateStaticPreview(accepted());
 assert.equal(result.published,false);
 assert.equal(result.needs_approval,true);
 assert.match(result.html,/<!doctype html>/);
 assert.match(result.html,/viewport/);
 assert.match(result.html,/noindex,nofollow/);
 assert.doesNotMatch(result.html,/<script/i);
 assert.doesNotMatch(result.html,/https?:\/\//i);
});
test('refuses malformed handoff',()=>{
 assert.throws(()=>generateStaticPreview({ok:true,may_start:true}),/Owner-reviewed/);
});
test('refuses unreviewed or auto-merge inputs',()=>{
 const h=accepted();h.brief.boundaries.automerge=true;
 assert.throws(()=>generateStaticPreview(h),/Insecure/);
});
test('escapes HTML injections from customer requirements',()=>{
 const h=accepted();h.brief.untrusted_customer_data.scope='<script>alert("x")</script> Build a site';
 const site=generateStaticPreview(h).html;
 assert.doesNotMatch(site,/<script>/);
 assert.match(site,/&lt;script&gt;/);
});
test('escapes quotes and ampersands',()=>{
 const h=accepted();h.brief.untrusted_customer_data.deliverables='A & B "included" with docs';
 const site=generateStaticPreview(h).html;
 assert.match(site,/A &amp; B &quot;included&quot;/);
});
test('rejects missing design scope and huge data',()=>{
 const h=accepted();h.brief.untrusted_customer_data.scope=' ';
 assert.throws(()=>generateStaticPreview(h),/Incomplete/);
 const j=accepted();j.brief.untrusted_customer_data.scope='a'.repeat(1801);
 assert.throws(()=>generateStaticPreview(j),/Incomplete/);
});
