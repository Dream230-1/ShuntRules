\
#!/usr/bin/env python3
from pathlib import Path
import argparse,json,sys
from common import load_yaml,read_rules,rule_key

def keys(path):return {rule_key(p):raw for _ln,raw,p in read_rules(path)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));ap.add_argument('--json-out',default='reports/adblock-collision.json');a=ap.parse_args();root=Path(a.root).resolve();m=load_yaml(root/'manifest.yaml');ad=keys(root/'.cache/remote-rules/AdvertisingLite.list');coll=[]
 for item in m['local_rulesets']:
  if item['policy']=='REJECT':continue
  for k,raw in keys(root/item['file']).items():
   if k in ad:coll.append({'ruleset':item['name'],'rule':raw,'ad_rule':ad[k]})
 ad_stage=next(x['stage'] for x in m['remote_rulesets'] if x['name']=='AdvertisingLite');order_errors=[x['name'] for x in m['local_rulesets']+m['remote_rulesets'] if x['name'] in m['route_audit']['critical_before_adblock'] and x['stage']>=ad_stage]
 report={'ok':not order_errors,'order_errors':order_errors,'exact_collisions':coll,'note':'精确碰撞仅报告；规则顺序错误会阻止发布。'};out=root/a.json_out;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2));sys.exit(0 if report['ok'] else 1)
if __name__=='__main__':main()
