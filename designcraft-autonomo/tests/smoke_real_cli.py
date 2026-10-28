"""Real DesignCraft CLI smoke test; creates a single-page document via MCP."""
import json
from pathlib import Path
import select
import subprocess
import time

root=Path('/tmp/designcraft-smoke').resolve()
input_dir=root/'inputs'
output_dir=root/'output'
input_dir.mkdir(parents=True,exist_ok=True)
output_dir.mkdir(parents=True,exist_ok=True)
proc=subprocess.Popen(['designcraft-cli','mcp','--automation-read-root',str(input_dir),'--automation-read-root',str(output_dir),'--automation-write-root',str(output_dir)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,cwd=str(root),text=True,bufsize=1)

def request(i,method,params=None,wait_seconds=80):
    payload={'jsonrpc':'2.0','id':i,'method':method}
    if params is not None: payload['params']=params
    proc.stdin.write(json.dumps(payload,ensure_ascii=False)+'\n')
    proc.stdin.flush()
    deadline=time.monotonic()+wait_seconds
    while time.monotonic()<deadline:
        ready,_,_=select.select([proc.stdout],[],[],min(5,max(.1,deadline-time.monotonic())))
        if not ready: continue
        line=proc.stdout.readline()
        if not line: raise RuntimeError('CLI exited or EOF')
        answer=json.loads(line)
        if answer.get('id')==i:
            if 'error' in answer: raise RuntimeError(f'{method} protocol error: {answer["error"]}')
            result=answer.get('result',{})
            if result.get('isError'): raise RuntimeError(f'{method} tool error: {str(result)[:800]}')
            print(f'{method}: OK',flush=True)
            return result
    raise TimeoutError(f'{method} timed out')

try:
    info=request(1,'initialize',{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'designcraft-ci-smoke','version':'1.0'}})
    assert info['serverInfo']['name'],info
    proc.stdin.write(json.dumps({'jsonrpc':'2.0','method':'notifications/initialized'})+'\n')
    proc.stdin.flush()
    listed=request(2,'tools/list')
    names={t['name'] for t in listed['tools']}
    for name in ('new_document','execute','render_page','save_document'):
        assert name in names, f'missing tool {name}'
    request(3,'tools/call',{'name':'new_document','arguments':{'preset':'A4','margins':36}})
    request(4,'tools/call',{'name':'execute','arguments':{'command':'frame.create','params':{'rect':[48,54,500,180],'content':'text','text':'DESIGNCRAFT MCP - SMOKE TEST'}}})
    request(5,'tools/call',{'name':'save_document','arguments':{'path':str(output_dir/'designcraft-smoke.designcraft')}})
    request(6,'tools/call',{'name':'render_page','arguments':{'page':0,'path':str(output_dir/'designcraft-smoke.png')}})
    assert (output_dir/'designcraft-smoke.designcraft').stat().st_size>100
    assert (output_dir/'designcraft-smoke.png').stat().st_size>100
    request(7,'tools/call',{'name':'execute','arguments':{'command':'file.exportPdf','params':{'path':str(output_dir/'designcraft-smoke.pdf')}}})
    assert (output_dir/'designcraft-smoke.pdf').read_bytes()[:4]==b'%PDF'
    print('REAL END-TO-END PASS - PDF, PNG and native file exist',flush=True)
finally:
    proc.terminate()
    try: proc.wait(timeout=5)
    except subprocess.TimeoutExpired: proc.kill()
