\
#!/usr/bin/env python3
from pathlib import Path
import argparse,json,statistics,time,requests,dns.message,dns.rdatatype
from common import load_yaml

def clean(u):return u.split('#',1)[0]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));ap.add_argument('--runs',type=int,default=3);ap.add_argument('--json-out',default='reports/dns-score.json');a=ap.parse_args();root=Path(a.root).resolve();m=load_yaml(root/'manifest.yaml');wire=dns.message.make_query('example.com',dns.rdatatype.A).to_wire();rows=[]
 for x in m['dns_catalog']:
  vals=[];errs=[]
  for _ in range(a.runs):
   t=time.perf_counter()
   try:
    r=requests.post(clean(x['url']),data=wire,headers={'Content-Type':'application/dns-message','Accept':'application/dns-message'},timeout=10);r.raise_for_status();dns.message.from_wire(r.content);vals.append((time.perf_counter()-t)*1000)
   except Exception as e:errs.append(str(e))
  rows.append({**x,'success':len(vals),'runs':a.runs,'median_ms':round(statistics.median(vals),1) if vals else None,'errors':errs})
 rows.sort(key=lambda z:(z['median_ms'] is None,z['median_ms'] or 1e9));report={'ok':True,'results':rows,'note':'只用于健康评分，不自动修改 Shadowrocket DNS 顺序；避免公共 Runner 波动改变设备配置。'};out=root/a.json_out;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
