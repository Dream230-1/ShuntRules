\
#!/usr/bin/env python3
from pathlib import Path
import argparse,json,sys
from common import domain_match,ip_match,load_yaml,parse_rule,read_rules,rule_policy

def compile_rules(root,m,online):
 rows=[]
 for item in sorted(m['inline_rules']+m['local_rulesets']+m['remote_rulesets'],key=lambda x:x['stage']):
  if 'rule' in item:rows.append((item['rule'],'Inline'))
  elif item in m['local_rulesets']:
   for _ln,raw,_p in read_rules(root/item['file']):rows.append((raw+','+item['policy'],item['name']))
  elif online:
   p=root/'.cache/remote-rules'/(item['name']+'.list')
   if p.exists():
    for _ln,raw,parts in read_rules(p):
     line=raw+','+item['policy'] if parts[-1]!='no-resolve' else ','.join(parts[:-1]+[item['policy'],'no-resolve'])
     rows.append((line,item['name']))
 rows.append((m['final_rule'],'FINAL'));return rows

def match(host,parts): return domain_match(host,parts) or ip_match(host,parts) or parts[0]=='FINAL'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));ap.add_argument('--online',action='store_true');ap.add_argument('--offline',action='store_true');ap.add_argument('--json-out',default='reports/regression.json');a=ap.parse_args();root=Path(a.root).resolve();m=load_yaml(root/'manifest.yaml');cases=load_yaml(root/'regression_cases.yaml')['cases'];rows=compile_rules(root,m,a.online);res=[]
 for c in cases:
  if c.get('online_only') and not a.online:continue
  found=None
  for idx,(raw,src) in enumerate(rows,1):
   p=parse_rule(raw)
   if p and match(c['host'],p):found={'policy':rule_policy(p),'source':src,'rule':raw,'order':idx};break
  ok=bool(found and found['policy']==c['expected_policy'] and (not c.get('source_contains') or c['source_contains'] in found['source']))
  res.append({'name':c['name'],'host':c['host'],'ok':ok,'expected_policy':c['expected_policy'],'actual':found})
 report={'ok':all(x['ok'] for x in res),'mode':'online' if a.online else 'offline','compiled_rule_count':len(rows),'results':res};out=root/a.json_out;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2));sys.exit(0 if report['ok'] else 1)
if __name__=='__main__':main()
