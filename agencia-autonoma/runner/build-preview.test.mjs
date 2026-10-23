import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,writeFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {qaHtml,buildSyntheticFiles,exportDemo,verifyDemo} from './build-preview.mjs';

test('produces valid, non-networked HTML and verifiable metadata',()=>{
 const files=buildSyntheticFiles();
 assert.deepEqual(Object.keys(files).sort(),['README.md','index.html','manifest.json','qa-report.json']);
 const report=qaHtml(files['index.html']);
 assert.equal(report.passed,true);
 assert.equal(Object.keys(report.checks).length,11);
 const metadata=JSON.parse(files['manifest.json']);
 assert.equal(metadata.actual_customer,false);
 assert.equal(metadata.claude_executed,false);
 assert.equal(metadata.bank_payment_verified,false);
 assert.equal(metadata.published,false);
});
test('rejects unsafe HTML from quality gate',()=>{
 const raw=buildSyntheticFiles()['index.html'];
 assert.equal(qaHtml(raw+'<script>steal()</script>').passed,false);
 assert.equal(qaHtml(raw+'<form><input type="password"></form>').passed,false);
 assert.equal(qaHtml(raw+'<img src="https://analytics.example/pixel">').passed,false);
});
test('creates a review-only artifact and detects tampering',async()=>{
 const root=await mkdtemp(join(tmpdir(),'agency-preview-qa-'));
 const out=join(root,'release');
 try {
  const first=await exportDemo(out);
  assert.equal(first.ok,true);
  assert.equal(first.checks,11);
  const result=await verifyDemo(out);
  assert.equal(result.sha256_html,first.sha256_html);
  await assert.rejects(()=>exportDemo(out),/EEXIST/);
  const old=await readFile(join(out,'index.html'),'utf8');
  await writeFile(join(out,'index.html'),old+'<!-- unauthorized edit -->');
  await assert.rejects(()=>verifyDemo(out),/Artifact validation failed/);
 }finally {
  await rm(root,{recursive:true,force:true});
 }
});
test('refuses relative destination paths',async()=>{
 await assert.rejects(()=>exportDemo('./somewhere'),/absolute destination path/);
});
