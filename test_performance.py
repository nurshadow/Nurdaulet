import json,unittest
from unittest.mock import patch
import server,reviewer
class PerformanceTests(unittest.TestCase):
 def test_compact_decisions(self):
  for value,allowed in [({'decision':'safe'},True),({'decision':'unsafe'},False),({'decision':'uncertain'},False),({'decision':'oops'},False),({'reason':'safe'},False),([],False)]:
   with patch.object(server,'ollama',return_value={'message':{'content':json.dumps(value)},'done_reason':'stop'}) as api:
    result=reviewer.check(server.ollama,[{'role':'user','content':'hello'}],'hello',False,compact=True)
    self.assertEqual(not result['blocked'],allowed)
    payload=api.call_args.args[1];self.assertEqual(payload['options']['num_predict'],32);self.assertFalse(payload['think'])
 def test_long_context_not_discarded(self):
  with patch.object(server,'ollama',return_value={'message':{'content':'{"decision":"safe"}'}}) as api:
   reviewer.check(api,[{'role':'user','content':'a'*4000}],'hello',False,compact=True)
   self.assertEqual(api.call_args.args[1]['options']['num_ctx'],8192)
 def test_truncated_safe_is_withheld(self):
  with patch.object(server,'ollama',return_value={'message':{'content':'{"decision":"safe"}'},'done_reason':'length'}) as api:
   self.assertTrue(reviewer.check(api,[],'hello',False,compact=True)['blocked'])
 def test_fast_chat_and_research_separate(self):
  def api(path,payload):
   if path=='/api/generate':return {}
   return {'message':{'content':'hello' if payload['model']==server.MODEL else '{"decision":"safe"}'},'done_reason':'stop'}
  with patch.object(server,'ollama',side_effect=api):
   r=server.infer([{'role':'user','content':'hello'}],'protected',use_reviewer=True,fast_chat=True)
   self.assertEqual(r['generation_options']['num_predict'],128);self.assertEqual(r['ai_review']['profile'],'compact_chat');self.assertEqual(r['answer'],'hello')
  with patch.object(server,'ollama',return_value={'message':{'content':'hello'}}):
   r=server.infer([{'role':'user','content':'hello'}],'protected',test=True,fast_chat=True)
   self.assertEqual(r['generation_options']['num_predict'],256);self.assertEqual(r['generation_options']['num_ctx'],4096)
