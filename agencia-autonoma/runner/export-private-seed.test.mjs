import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,readFile,lstat,symlink,rm} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {createHash} from 'node:crypto';
import {buildPrivateSeed} from './export-private-seed.mjs';

const skills=['agencia-arquitecto','agencia-cobranzas','agencia-entregas','agencia-estimador','agencia-intake','agencia-programador','agencia-prospeccion','agencia-qa','agencia-soporte'];
async function fixture(fn){
 const temp=await mkdtemp(join(tmpdir(),'agency-seed-'));
 const source=join(temp,'source'),output=join(temp,'private-seed');
 try{
  for(const folder of ['agencia-autonoma/site','agencia-autonoma/neon','agencia-autonoma/sql','agencia-autonoma/tests','agencia-autonoma/runner'])
   await mkdir(join(source,folder),{recursive:true});
  const files={
   'agencia-autonoma/site/index.html':'<h1>Agencia de prueba</h1>',
   'agencia-autonoma/neon/index.mjs':'export const ok=true;',
   'agencia-autonoma/sql/schema.sql':'CREATE TABLE sample (id int);',
   'agencia-autonoma/tests/a.test.mjs':'export const testFixture=true;',
   'agencia-autonoma/runner/a.mjs':'export const fixture=true;'
  };
  for(const [p,txt] of Object.entries(files))await writeFile(join(source,p),txt);
  for(const s of skills){
   const d=join(source,'.claude/skills',s);await mkdir(d,{recursive:true});
   await writeFile(join(d,'SKILL.md'),'---\nname: '+s+'\n---\n');
  }
  await writeFile(join(source,'freellmapi-secret.txt'),'outside allowlist');
  return await fn({temp,source,output,files});
 }finally{await rm(temp,{recursive:true,force:true})}
}
const opts=({source,output})=>({sourceRoot:source,outputDir:output,targetRepo:'adedramaa/agencia-privada'});
test('only agency code and nine agency skills are packaged, no sibling app',async()=>fixture(async ctx=>{
 const result=await buildPrivateSeed(opts(ctx));
 assert.equal(result.ok,true);
 assert.equal(result.manual_private_repo_creation_required,true);
 const manifest=JSON.parse(await readFile(join(ctx.output,'migration-manifest.json'),'utf8'));
 assert.equal(manifest.excludes_crm_records,true);
 assert.equal(manifest.ci_only_manual,true);
 assert.equal(manifest.files.length,16);
 assert.equal(manifest.files.filter(f=>f.path.endsWith('/SKILL.md')).length,9);
 assert.equal(manifest.files.some(f=>f.path.includes('freellmapi-secret')),false);
 const wf=await readFile(join(ctx.output,'.github/workflows/agency-qa.yml'),'utf8');
 assert.match(wf,/workflow_dispatch/);
 assert.match(wf,/github.repository == 'adedramaa\/agencia-privada'/);
 assert.doesNotMatch(wf,/^\s+push:/m);
 for(const [name,content] of Object.entries(ctx.files)){
  const hash=createHash('sha256').update(content).digest('hex');
  assert.equal(manifest.files.find(f=>f.path===name)?.sha256,hash);
 }
}));
test('fails closed if destination already exists',async()=>fixture(async ctx=>{
 await mkdir(ctx.output);
 await assert.rejects(buildPrivateSeed(opts(ctx)),/output_already_exists/);
 const st=await lstat(ctx.output);
 assert.equal(st.isDirectory(),true);
}));
test('refuses path traversal and mis-scoped repository',async()=>fixture(async ctx=>{
 for(const name of ['other','owner/..','owner/.hidden','owner/repo.git','owner/repo/another']){
  await assert.rejects(buildPrivateSeed({...opts(ctx),targetRepo:name}),/invalid_target_repository/);
 }
 await assert.rejects(buildPrivateSeed({...opts(ctx),outputDir:ctx.source}),/output_must_be_outside_source/);
 await assert.rejects(buildPrivateSeed({...opts(ctx),outputDir:join(ctx.source,'staging')}),/output_must_be_outside_source/);
}));
test('rejects symlink in source before writing anything',async()=>fixture(async ctx=>{
 await symlink(join(ctx.source,'freellmapi-secret.txt'),join(ctx.source,'agencia-autonoma/site/leak.txt'));
 await assert.rejects(buildPrivateSeed(opts(ctx)),/symlink_rejected/);
 await assert.rejects(lstat(ctx.output),{code:'ENOENT'});
}));
test('rejects unknown extension and known secret patterns before export',async()=>fixture(async ctx=>{
 const path=join(ctx.source,'agencia-autonoma/neon','credentials.env');
 await writeFile(path,'SENSITIVE=no');
 await assert.rejects(buildPrivateSeed(opts(ctx)),/unexpected_extension/);
 await rm(path);
 await writeFile(join(ctx.source,'agencia-autonoma/neon/index.mjs'),'const fake="gh'+'p_abcdefghijklmnopqrstuvwxyz123456";');
 await assert.rejects(buildPrivateSeed(opts(ctx)),/possible_secret_in_source/);
 await assert.rejects(lstat(ctx.output),{code:'ENOENT'});
}));
