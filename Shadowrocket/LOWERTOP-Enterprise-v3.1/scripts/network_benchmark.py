\
#!/usr/bin/env python3
from pathlib import Path
import argparse,json,statistics,time,requests
from common import load_yaml

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));ap.add_argument('--proxy');ap.add_argument('--runs',type=int,default=3);ap.add_argument('--json-out',default='reports/network-benchmark.json');a=ap.parse_args();root=Path(a.root).resolve();m=load_yaml(root/'manifest.yaml');proxies={'http':a.proxy,'https':a.proxy} if a.proxy else None;rows=[]
 for e in m['benchmark_endpoints']:
  vals=[];codes=[];errors=[]
  for _ in range(a.runs):
   t=time.perf_counter()
   try:r=requests.get(e['url'],timeout=15,proxies=proxies,allow_redirects=False);vals.append((time.perf_counter()-t)*1000);codes.append(r.status_code)
   except Exception as ex:errors.append(str(ex))
  rows.append({'id':e['id'],'url':e['url'],'success':len(vals),'runs':a.runs,'median_ms':round(statistics.median(vals),1) if vals else None,'min_ms':round(min(vals),1) if vals else None,'max_ms':round(max(vals),1) if vals else None,'http_statuses':codes,'errors':errors})
 report={'ok':True,'proxy':a.proxy,'results':rows,'note':'非阻断报告；公共 Runner 绝对延迟不能代表 iPhone。'};out=root/a.json_out;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
