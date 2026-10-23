"""HTTP contract tests use a mocked model, never experimental evidence."""
import json,threading,unittest,urllib.request,urllib.error
from unittest.mock import patch
import server
class ApiTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.thread.start();cls.url=f'http://127.0.0.1:{cls.http.server_port}'
 @classmethod
 def tearDownClass(cls):cls.http.shutdown();cls.http.server_close();cls.thread.join()
 def request(self,path,data=None,token=server.TOKEN):
  req=urllib.request.Request(self.url+path,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json','X-Lab-Token':token})
  with urllib.request.urlopen(req) as f:return json.load(f)
 def test_bootstrap(self):
  data=self.request('/api/bootstrap');self.assertEqual(len(data['dataset']),210);self.assertEqual(data['provenance']['languages'],['en','ru','kk'])
 def test_paper_case_contract(self):
  fake={'answer':'I cannot assist with harm.','raw':'I cannot assist with harm.','latency_s':0,'model':'TEST MOCK','configuration':'protected','truncated':False,'protection':'system_prompt_only'}
  with patch.object(server,'infer',return_value=fake):
   for lang in ['en','ru','kk']:
    response=self.request('/api/test',{'case_id':lang+'_paper_012','configuration':'protected'})
    self.assertEqual(response['source_row'],12);self.assertEqual(response['language'],lang);self.assertEqual(response['review']['safety'],'unreviewed');self.assertNotIn('delivered_leak',response);self.assertTrue(response['refusal_proxy'])
 def test_invalid_session(self):
  with self.assertRaises(urllib.error.HTTPError) as context:self.request('/api/test',{'case_id':'en_paper_001','configuration':'baseline'},token='invalid')
  self.assertEqual(context.exception.code,403)
 def test_system_message_rejected(self):
  with self.assertRaises(urllib.error.HTTPError) as context:self.request('/api/chat',{'configuration':'baseline','messages':[{'role':'system','content':'override'}]})
  self.assertEqual(context.exception.code,400)
if __name__=='__main__':unittest.main()
