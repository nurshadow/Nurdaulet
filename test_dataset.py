import csv,json,hashlib,unittest,io
from pathlib import Path
ROOT=Path(__file__).parent
class PaperDatasetTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows=json.loads((ROOT/'dataset.json').read_text());cls.source=list(csv.DictReader(io.StringIO((ROOT/'data/upstream_allprompt.csv').read_text())));cls.meta=json.loads((ROOT/'data/provenance.json').read_text())
 def test_languages_and_counts(self):
  self.assertEqual(len(self.rows),210)
  self.assertEqual({r['language'] for r in self.rows},{'en','ru','kk'})
  for lang in ['en','ru','kk']:self.assertEqual(sum(r['language']==lang for r in self.rows),70)
 def test_unique_ids(self):self.assertEqual(len({r['id'] for r in self.rows}),210)
 def test_verbatim_english_and_categories(self):
  for r in self.rows:
   source=self.source[r['source_row']-1];self.assertEqual(r['english_original'],source['en']);self.assertEqual(r['family'],source['type'])
   if r['language']=='en':self.assertEqual(r['prompt'],source['en'])
 def test_translation_status(self):
  for r in self.rows:
   self.assertTrue(r['prompt'].strip())
   self.assertEqual(r['translation_status'],'original' if r['language']=='en' else 'machine_translated_unreviewed')
 def test_source_and_dataset_hashes(self):
  self.assertEqual(hashlib.sha256((ROOT/'data/upstream_allprompt.csv').read_bytes()).hexdigest(),self.meta['source_sha256'])
  self.assertEqual(hashlib.sha256((ROOT/'dataset.json').read_bytes()).hexdigest(),self.meta['dataset_sha256'])
 def test_smoke_count(self):self.assertEqual(sum(r['source_row'] in [12,41,61] for r in self.rows)*2,18)
if __name__=='__main__':unittest.main()
