\
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from common import load_yaml
class V31(unittest.TestCase):
 def setUp(self):self.m=load_yaml(ROOT/'manifest.yaml')
 def test_profiles(self):self.assertIn('performance',self.m['profiles']);self.assertFalse(self.m['general_common']['ipv6'])
 def test_adblock_order(self):
  ad=next(x['stage'] for x in self.m['remote_rulesets'] if x['name']=='AdvertisingLite')
  self.assertTrue(all(x['stage']<ad for x in self.m['local_rulesets']))
 def test_ai_split(self):self.assertEqual([x['name'] for x in self.m['local_rulesets'] if x['policy']=='AI'][:2],['AI-Core','AI-Realtime'])
if __name__=='__main__':unittest.main()
