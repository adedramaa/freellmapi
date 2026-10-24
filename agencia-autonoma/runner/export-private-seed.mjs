/**
 * Creates an offline, allowlisted seed for a FUTURE dedicated private agency repo.
 * Does not create a repository, read live CRM data, send requests or deploy anything.
 * CLI: node agencia-autonoma/runner/export-private-seed.mjs --output /absolute/new-directory --target owner/repo
 */
import {readdir,readFile,mkdir,writeFile,copyFile,lstat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve,relative,dirname,join,extname,isAbsolute,sep} from 'node:path';
import {fileURLToPath} from 'node:url';

const SOURCE=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const FOLDERS=Object.freeze({
  'agencia-autonoma/site':new Set(['.html','.xml','.txt','.css','.js','.svg','.webp','.png','.jpg','.jpeg','.ico','.webmanifest']),
  'agencia-autonoma/neon':new Set(['.mjs']),
  'agencia-autonoma/sql':new Set(['.sql']),
  'agencia-autonoma/tests':new Set(['.mjs']),
  'agencia-autonoma/runner':new Set(['.mjs'])
});
const SKILLS=['agencia-arquitecto','agencia-cobranzas','agencia-entregas','agencia-estimador','agencia-intake','agencia-programador','agencia-prospeccion','agencia-qa','agencia-soporte'];
const SECRET=/(?:-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|github_pat_[A-Za-z0-9_]{15,}|gh[pousr]_[A-Za-z0-9]{25,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9_-]{25,})/;
const limit={files:200,bytes:12_000_000};

function validateTarget(target){
 if(typeof target!=='string'||!/^[a-z\d](?:[a-z\d-]{0,38})\/[A-Za-z0-9._-]{1,100}$/i.test(target))
   throw Error('invalid_target_repository');
 const repo=target.split('/')[1];
 if(repo==='.'||repo==='..'||repo.endsWith('.git')||repo.startsWith('.'))throw Error('invalid_target_repository');
 return target;
}
function inside(base,dest){
 const rel=relative(base,dest);
 return rel===''||(!rel.startsWith('..'+sep)&&rel!=='..'&&!isAbsolute(rel));
}
function sha(buf){return createHash('sha256').update(buf).digest('hex');}
function guardSecrets(buffer,name){
 const t=buffer.toString('utf8');
 if(SECRET.test(t))throw Error('possible_secret_in_source:'+name);
}
async function collect(root,folder,extensions,result){
 const full=join(root,folder);
 const st=await lstat(full);
 if(st.isSymbolicLink()||!st.isDirectory())throw Error('unsafe_folder:'+folder);
 for(const entry of (await readdir(full,{withFileTypes:true})).sort((a,b)=>a.name.localeCompare(b.name))){
  if(entry.name.startsWith('.'))throw Error('hidden_file_requires_review:'+folder+'/'+entry.name);
  const rel=join(folder,entry.name);
  if(entry.isSymbolicLink())throw Error('symlink_rejected:'+rel);
  if(entry.isDirectory())await collect(root,rel,extensions,result);
  else if(entry.isFile()){
   if(!extensions.has(extname(entry.name)))throw Error('unexpected_extension:'+rel);
   result.push(rel);
  }else throw Error('unsafe_entry:'+rel);
 }
}
export async function buildPrivateSeed({sourceRoot,outputDir,targetRepo}){
 const target=validateTarget(targetRepo),root=resolve(sourceRoot);
 if(!isAbsolute(outputDir))throw Error('output_must_be_absolute');
 const output=resolve(outputDir);
 if(inside(root,output)||inside(output,root))throw Error('output_must_be_outside_source');
 try{await lstat(output);throw Error('output_already_exists');}
 catch(e){if(e.code!=='ENOENT')throw e;}
 const files=[];
 for(const [folder,extensions] of Object.entries(FOLDERS))await collect(root,folder,extensions,files);
 for(const name of SKILLS){
  const p='.claude/skills/'+name+'/SKILL.md';
  if(!(await lstat(join(root,p))).isFile())throw Error('missing_skill:'+name);
  files.push(p);
 }
 if(files.length>limit.files)throw Error('too_many_files');
 let bytes=0;
 const copies=[];
 for(const name of files.sort()){
  const path=join(root,name),st=await lstat(path);
  if(!st.isFile()||st.isSymbolicLink())throw Error('unsafe_file:'+name);
  const buffer=await readFile(path);
  bytes+=buffer.length;
  if(bytes>limit.bytes)throw Error('bundle_too_large');
  if(!['.png','.jpg','.jpeg','.webp','.ico'].includes(extname(name)))guardSecrets(buffer,name);
  copies.push({name,buffer,sha256:sha(buffer)});
 }
 // All verification takes place before creating the destination directory.
 await mkdir(output,{recursive:false});
 try{
  for(const c of copies){
   const dest=join(output,c.name);
   await mkdir(dirname(dest),{recursive:true});
   await writeFile(dest,c.buffer,{flag:'wx'});
  }
  const workflow=[
   'name: Agencia privada - QA manual',
   'on:',
   '  workflow_dispatch:',
   'permissions:',
   '  contents: read',
   'jobs:',
   '  safe-tests:',
   "    if: github.repository == '"+target+"'",
   '    runs-on: ubuntu-24.04',
   '    timeout-minutes: 6',
   '    steps:',
   '      - uses: actions/checkout@v4',
   '        with:',
   '          persist-credentials: false',
   '      - name: Tests sin credenciales ni acceso a clientes',
   '        run: |',
   '          node --test agencia-autonoma/tests/*.test.mjs',
   '          node --test agencia-autonoma/runner/*.test.mjs'
  ].join('\n')+'\n';
  const wf='.github/workflows/agency-qa.yml';
  await mkdir(join(output,'.github/workflows'),{recursive:true});
  await writeFile(join(output,wf),workflow,{flag:'wx'});
  const readme=[
   '# Autónoma Dev — plantilla de repositorio PRIVADO',
   '',
   'Exportación local de código únicamente. NO es un repositorio creado, una migración ni un despliegue.',
   'Destino previsto: '+target+' (comprobar que exista y sea PRIVADO antes de subir contenido).',
   '',
   'Incluye solo site, neon, sql, tests, runner y nueve skills de la agencia.',
   'Excluye FreeLLMAPI, Mayor Studio, Raíces, informes con datos, .env, credenciales y base de datos.',
   'El QA nuevo es MANUAL; no activa ejecuciones automáticas ni gastos.',
   'Antes de operar: verificar privacidad real del repo, permisos, secretos en vault,',
   'dominios y configuraciones, iniciar sesión como dueño, probar POST controlado,',
   'cobros/facturación, y ejecución de Claude Code con aprobación humana.',
   'No cargar datos reales de clientes hasta pasar revisión de seguridad.',
   ''
  ].join('\n');
  const doc='README_PRIVATE_MIGRATION.md';
  await writeFile(join(output,doc),readme,{flag:'wx'});
  const manifest={version:'agency-private-seed-v1',intended_private_repository:target,
    excludes_crm_records:true,includes_secrets:false,ci_only_manual:true,
    files:[...copies.map(c=>({path:c.name,sha256:c.sha256})),
      {path:wf,sha256:sha(Buffer.from(workflow))},{path:doc,sha256:sha(Buffer.from(readme))}]};
  await writeFile(join(output,'migration-manifest.json'),JSON.stringify(manifest,null,2)+'\n',{flag:'wx'});
  return {ok:true,files:manifest.files.length,bytes,target,output,manual_private_repo_creation_required:true};
 }catch(e){
  // Never attempt to remove pre-existing data. The output is guaranteed new.
  const {rm}=await import('node:fs/promises');
  await rm(output,{recursive:true,force:true});
  throw e;
 }
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const args=process.argv.slice(2);
 const get=k=>{const i=args.indexOf(k);return i>=0?args[i+1]:undefined};
 if(args.length!==4||!get('--output')||!get('--target')){console.error('Usage: --output /absolute/new-dir --target owner/repo');process.exitCode=2;}
 else buildPrivateSeed({sourceRoot:SOURCE,outputDir:get('--output'),targetRepo:get('--target')})
  .then(r=>console.log(JSON.stringify(r))).catch(e=>{console.error(e.message);process.exitCode=1});
}
