import json, unittest
from unittest.mock import patch
import reviewer, server
class GateTests(unittest.TestCase):
 def test_decisions_and_unloading(self):
  for decision in ['safe','unsafe','uncertain','invalid']:
   def api(path,payload):
    if path=='/api/generate':return {}
    content='CANDIDATE' if payload['model']==server.MODEL else ('invalid' if decision=='invalid' else json.dumps({'decision':decision,'reason':'Test assessment'}))
    return {'message':{'content':content},'done_reason':'stop'}
   with patch.object(server,'ollama',side_effect=api) as mock:
    result=server.infer([{'role':'user','content':'hello'}],'protected',use_reviewer=True)
    self.assertEqual(result['answer']=='CANDIDATE',decision=='safe')
    self.assertEqual(mock.call_args_list[1].args[1]['keep_alive'],0)
    self.assertEqual(mock.call_args_list[2].args[1]['keep_alive'],0)
 def test_timeout(self):
  with patch.object(server,'ollama',side_effect=TimeoutError):
   self.assertTrue(reviewer.check(server.ollama,[], 'candidate',False)['blocked'])
 def test_limit(self):
  with patch.object(server,'ollama') as api:
   self.assertEqual(reviewer.check(api,[{'role':'user','content':'a'*6100}],'candidate',False)['status'],'input_limit')
   api.assert_not_called()
 def test_disabled(self):
  with patch.object(server,'ollama',return_value={'message':{'content':'candidate'}}) as api:
   r=server.infer([{'role':'user','content':'hello'}],'protected')
   self.assertEqual(r['answer'],'candidate');self.assertNotIn('ai_review',r);self.assertEqual(api.call_count,1)
