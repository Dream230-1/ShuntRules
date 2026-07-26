\
#!/usr/bin/env python3
from pathlib import Path
import argparse,json,sys

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));ap.add_argument('--json-out',default='reports/ruleset-drift.json');a=ap.parse_args();root=Path(a.root).resolve();cur=json.loads((root/'reports/remote-audit.json').read_text(encoding='utf-8'));base=json.loads((root/'baselines/remote-rules.json').read_text(encoding='utf-8'));b={x['name']:x for x in base['results']};rows=[];hard=[]
 for x in cur['results']:
  old=b.get(x['name']);delta=None if not old else {'sha_changed':old.get('sha256')!=x.get('sha256'),'rule_delta':x['rule_count']-old['rule_count'],'byte_delta':x['bytes']-old['bytes']}
  if not old:hard.append(f'缺少基线：{x["name"]}')
  elif abs(delta['rule_delta'])>max(10,int(old['rule_count']*.2)):hard.append(f'{x["name"]} 规则数漂移过大')
  rows.append({'name':x['name'],'baseline':old,'current':{'sha256':x['sha256'],'rule_count':x['rule_count'],'bytes':x['bytes']},'delta':delta})
 report={'ok':not hard,'errors':hard,'results':rows};out=root/a.json_out;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2));sys.exit(0 if report['ok'] else 1)
if __name__=='__main__':main()
