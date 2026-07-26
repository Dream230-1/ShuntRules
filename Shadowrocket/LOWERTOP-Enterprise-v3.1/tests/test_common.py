\
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from common import load_yaml,domain_match,ip_match
class T(unittest.TestCase):
 def test_includes(self):self.assertEqual(load_yaml(ROOT/'manifest.yaml')['meta']['version'],'3.1.0-rc1')
 def test_domain(self):self.assertTrue(domain_match('ios.chat.openai.com',['DOMAIN-SUFFIX','openai.com']))
 def test_ip(self):self.assertTrue(ip_match('149.154.167.222',['IP-CIDR','149.154.164.0/22']))
 def test_no_keyword(self):self.assertFalse(domain_match('openai.example.org',['DOMAIN-SUFFIX','openai.com']))
if __name__=='__main__':unittest.main()
