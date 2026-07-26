\
#!/usr/bin/env python3
from pathlib import Path
import argparse,json,sys
from common import BUILTIN_POLICIES,load_yaml,read_rules

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));ap.add_argument('--json-out',default='reports/config-audit.json');a=ap.parse_args();root=Path(a.root).resolve();m=load_yaml(root/'manifest.yaml');errors=[];warnings=[]
 groups={g['name'] for g in m['proxy_groups']};valid=BUILTIN_POLICIES|groups
 names=[]
 for section in ['local_rulesets','remote_rulesets']:
  for x in m[section]:
   if x['name'] in names:errors.append(f'重复规则集名称：{x["name"]}')
   names.append(x['name'])
   if x['policy'] not in valid:errors.append(f'未知策略：{x["name"]} → {x["policy"]}')
 for x in m['local_rulesets']:
  p=root/x['file']
  if not p.exists():errors.append(f'本地规则文件不存在：{x["file"]}')
  elif not read_rules(p):warnings.append(f'本地规则为空：{x["file"]}')
 ad=next((x['stage'] for x in m['remote_rulesets'] if x['name']=='AdvertisingLite'),None)
 if ad is None:errors.append('AdvertisingLite 缺失')
 else:
  for name in m.get('route_audit',{}).get('critical_before_adblock',[]):
   items=m['local_rulesets']+m['remote_rulesets'];obj=next((x for x in items if x['name']==name),None)
   if not obj:errors.append(f'关键规则集缺失：{name}')
   elif obj['stage']>=ad:errors.append(f'{name} 必须位于 AdvertisingLite 前')
 report={'ok':not errors,'version':m['meta']['version'],'errors':errors,'warnings':warnings};out=root/a.json_out;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2));sys.exit(0 if report['ok'] else 1)
if __name__=='__main__':main()
