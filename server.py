"""Local-only multilingual chatbot and evaluation API. Python standard library."""
import argparse,json,mimetypes,secrets,threading,time,urllib.request,urllib.error
from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from paper_policy import BASELINE,PROTECTED,refusal
ROOT=Path(__file__).parent
DATA=json.loads((ROOT/'dataset.json').read_text())
MODEL='llama3:latest'; OLLAMA='http://127.0.0.1:11434'; LOCK=threading.Lock(); TOKEN=secrets.token_urlsafe(32)
def ollama(path,payload=None):
 req=urllib.request.Request(OLLAMA+path,data=json.dumps(payload).encode() if payload is not None else None,headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=300 if payload else 5) as f:return json.load(f)
def infer(messages,mode,test=False):
 if not LOCK.acquire(blocking=False):raise RuntimeError('Another model request is running. Please wait for it to finish.')
 try:
  start=time.perf_counter()
  response=ollama('/api/chat',{'model':MODEL,'stream':False,'messages':[{'role':'system','content':BASELINE if mode=='baseline' else PROTECTED}]+messages,'options':{'temperature':0,'seed':42,'num_ctx':4096,'num_predict':256},'keep_alive':'10m'})
  raw=response['message']['content'];delivered=raw
  return {'answer':delivered,'raw':raw,'protection':'system_prompt_only','latency_s':round(time.perf_counter()-start,3),'model':MODEL,'configuration':mode,'truncated':response.get('done_reason')=='length','created_at':response.get('created_at'),'eval_count':response.get('eval_count')}
 finally:LOCK.release()
class Handler(BaseHTTPRequestHandler):
 def send_json(self,data,status=200):
  body=json.dumps(data,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
 def allowed(self):
  host=self.headers.get('Host','');port=self.server.server_port
  return host in [f'127.0.0.1:{port}',f'localhost:{port}']
 def do_GET(self):
  if not self.allowed():return self.send_json({'error':'Local host required.'},403)
  path=self.path.split('?')[0]
  if path=='/api/bootstrap':return self.send_json({'token':TOKEN,'model':MODEL,'dataset':DATA,'provenance':json.loads((ROOT/'data/provenance.json').read_text())})
  if path=='/api/status':
   try:
    models=ollama('/api/tags').get('models',[]);found=next((m for m in models if m['name']==MODEL),None)
    return self.send_json({'connected':bool(found),'model':MODEL,'digest':found['digest'] if found else None,'error':None if found else f'Install the model with: ollama pull {MODEL}'})
   except Exception:return self.send_json({'connected':False,'model':MODEL,'error':'Start the Ollama application or run ollama serve, then reconnect.'})
  files={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}
  if path not in files:return self.send_json({'error':'Not found'},404)
  f=ROOT/'static'/files[path];body=f.read_bytes();self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(str(f))[0]+'; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'");self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
 def do_POST(self):
  if not self.allowed() or self.headers.get('X-Lab-Token')!=TOKEN:return self.send_json({'error':'Invalid local session. Reload the page.'},403)
  origin=self.headers.get('Origin')
  if origin and origin not in [f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}']:return self.send_json({'error':'Cross-origin requests are not allowed.'},403)
  try:
   length=int(self.headers.get('Content-Length','0'))
   if not 0<length<=128000:raise ValueError('Request must contain less than 128 KB.')
   body=json.loads(self.rfile.read(length));mode=body.get('configuration')
   if mode not in ['baseline','protected']:raise ValueError('Choose baseline or protected mode.')
   if self.path=='/api/chat':
    msgs=body.get('messages')
    if not isinstance(msgs,list) or not 1<=len(msgs)<=20:raise ValueError('Start a new chat after 10 turns.')
    if any(not isinstance(m,dict) or m.get('role') not in ['user','assistant'] or not isinstance(m.get('content'),str) or not 0<len(m['content'])<=12000 for m in msgs):raise ValueError('Invalid message or message longer than 12,000 characters.')
    if msgs[-1]['role']!='user':raise ValueError('The last message must be from the user.')
    if sum(len(m['content']) for m in msgs)>32000:raise ValueError('Conversation is too long. Start a new chat.')
    result=infer([{'role':m['role'],'content':m['content']} for m in msgs],mode);result.pop('raw');return self.send_json(result)
   if self.path=='/api/test':
    case=next((r for r in DATA if r['id']==body.get('case_id')),None)
    if not case:raise ValueError('Unknown test case.')
    result=infer([{'role':'user','content':case['prompt']}],mode,True)
    return self.send_json({**case,**result,'refusal_proxy':refusal(result['answer']),'review':{'rejection':'unreviewed','relevance':'unreviewed','safety':'unreviewed','notes':''}})
   return self.send_json({'error':'Not found'},404)
  except (ValueError,TypeError,KeyError) as e:return self.send_json({'error':str(e)},400)
  except RuntimeError as e:return self.send_json({'error':str(e)},409)
  except (urllib.error.URLError,TimeoutError):return self.send_json({'error':'Ollama did not respond. Check it is running and retry.'},503)
  except Exception as e:print(type(e).__name__,str(e),flush=True);return self.send_json({'error':'The local model request failed. Check the terminal log.'},500)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8765);a=p.parse_args()
 server=ThreadingHTTPServer(('127.0.0.1',a.port),Handler)
 print(f'Local chatbot: http://127.0.0.1:{a.port}',flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:server.server_close()
