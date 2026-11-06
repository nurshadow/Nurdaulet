"""Local-only multilingual chatbot and evaluation API. Python standard library."""
import argparse,json,mimetypes,secrets,threading,time,urllib.request,urllib.error
from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from paper_policy import BASELINE,PROTECTED,refusal
import reviewer
ROOT=Path(__file__).parent
DATA=json.loads((ROOT/'dataset.json').read_text())
MODEL='llama3:latest'; OLLAMA='http://127.0.0.1:11434'; LOCK=threading.Lock(); TOKEN=secrets.token_urlsafe(32)
def ollama(path,payload=None):
 req=urllib.request.Request(OLLAMA+path,data=json.dumps(payload).encode() if payload is not None else None,headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=300 if payload else 5) as f:return json.load(f)
def infer(messages,mode,test=False,use_reviewer=False,fast_chat=False):
 if not LOCK.acquire(blocking=False):raise RuntimeError('Another model request is running. Please wait for it to finish.')
 try:
  start=time.perf_counter()
  fast_chat=fast_chat and not test
  instruction=BASELINE if mode=='baseline' else PROTECTED
  generation_options={'temperature':0,'seed':42,'num_ctx':4096,'num_predict':256}
  if fast_chat:
   size=len(json.dumps([{'role':'system','content':instruction}]+messages,ensure_ascii=False).encode('utf-8'))+512
   generation_options['num_ctx']=2048 if size<=2048 else 4096
   generation_options['num_predict']=128
  if use_reviewer:
   # Explicit unloading avoids keeping both models resident on an 8 GB Mac.
   ollama('/api/generate',{'model':reviewer.MODEL,'keep_alive':0})
  response=ollama('/api/chat',{'model':MODEL,'stream':False,'messages':[{'role':'system','content':BASELINE if mode=='baseline' else PROTECTED}]+messages,'options':generation_options,'keep_alive':0 if use_reviewer else '10m'})
  raw=response['message']['content'];delivered=raw
  generation_s=round(time.perf_counter()-start,3)
  assessment=None
  if use_reviewer:
   assessment=reviewer.check(ollama,messages,raw,response.get('done_reason')=='length',compact=fast_chat)
   if assessment['blocked']:
    delivered=('I cannot provide that response because it may help cause harm. Please ask for a safe alternative.' if assessment['decision']=='unsafe' else 'I could not verify that this response is safe, so it has been withheld. Please rephrase your request or start a new chat.')
  result={'answer':delivered,'raw':raw,'protection':'system_prompt_plus_reviewer' if use_reviewer else 'system_prompt_only','latency_s':round(time.perf_counter()-start,3),'generation_latency_s':generation_s,'generation_options':generation_options,'performance_profile':'fast_chat' if fast_chat else 'research','model':MODEL,'configuration':mode,'truncated':response.get('done_reason')=='length','created_at':response.get('created_at'),'eval_count':response.get('eval_count')}
  if assessment is not None:result['ai_review']=assessment
  return result
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
    return self.send_json({'connected':bool(found),'model':MODEL,'digest':found['digest'] if found else None,'reviewer_available':any(m['name']==reviewer.MODEL for m in models),'reviewer_model':reviewer.MODEL,'error':None if found else f'Install the model with: ollama pull {MODEL}'})
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
   if mode not in (['baseline','protected','protected_qwen'] if self.path=='/api/test' else ['baseline','protected']):raise ValueError('Choose baseline or protected mode.')
   if self.path=='/api/chat':
    fast_chat=body.get('fast_chat',False)
    if not isinstance(fast_chat,bool):raise ValueError('Invalid performance setting.')
    use_reviewer=body.get('use_reviewer',False)
    if not isinstance(use_reviewer,bool):raise ValueError('Invalid reviewer setting.')
    msgs=body.get('messages')
    if not isinstance(msgs,list) or not 1<=len(msgs)<=20:raise ValueError('Start a new chat after 10 turns.')
    if any(not isinstance(m,dict) or m.get('role') not in ['user','assistant'] or not isinstance(m.get('content'),str) or not 0<len(m['content'])<=12000 for m in msgs):raise ValueError('Invalid message or message longer than 12,000 characters.')
    if msgs[-1]['role']!='user':raise ValueError('The last message must be from the user.')
    if sum(len(m['content']) for m in msgs)>32000:raise ValueError('Conversation is too long. Start a new chat.')
    result=infer([{'role':m['role'],'content':m['content']} for m in msgs],mode,use_reviewer=use_reviewer,fast_chat=fast_chat);result.pop('raw')
    if 'ai_review' in result:result['ai_review'].pop('reason',None)
    return self.send_json(result)
   if self.path=='/api/test':
    case=next((r for r in DATA if r['id']==body.get('case_id')),None)
    if not case:raise ValueError('Unknown test case.')
    result=infer([{'role':'user','content':case['prompt']}],'protected' if mode=='protected_qwen' else mode,True,use_reviewer=mode=='protected_qwen')
    result['configuration']=mode
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
