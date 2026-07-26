\
#!/usr/bin/env python3
from pathlib import Path
import argparse,json,sys,time,requests
from common import load_yaml

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));ap.add_argument('--proxy');ap.add_argument('--allow-warnings',action='store_true');ap.add_argument('--allow-failures',action='store_true');ap.add_argument('--json-out',default='reports/service-health.json');a=ap.parse_args();root=Path(a.root).resolve();m=load_yaml(root/'manifest.yaml');proxies={'http':a.proxy,'https':a.proxy} if a.proxy else None;rows=[]
 for x in m['health_checks']:
  t=time.perf_counter();status='FAIL';code=None;err=None;body_ok=True
  try:
   r=requests.request(x.get('method','GET'),x['url'],timeout=x.get('timeout',12),proxies=proxies,allow_redirects=False);code=r.status_code;lat=(time.perf_counter()-t)*1000
   if x.get('body_contains'):body_ok=x['body_contains'].lower() in r.text.lower()
   status='PASS' if code in x['healthy_status'] and body_ok and lat<=x.get('max_latency_ms',999999) else 'WARN' if code in x.get('warning_status',[]) or lat>x.get('max_latency_ms',999999) else 'FAIL'
  except Exception as e:lat=(time.perf_counter()-t)*1000;err=str(e)
  rows.append({'id':x['id'],'service':x['service'],'policy':x['policy'],'url':x['url'],'status':status,'http_status':code,'latency_ms':round(lat,1),'error':err})
 summary={k:sum(r['status']==k for r in rows) for k in ['PASS','WARN','FAIL']};ok=summary['FAIL']==0 or a.allow_failures
 report={'ok':ok,'proxy':a.proxy,'summary':summary,'results':rows,'note':'公共 Runner 只检查端点，不代表 iPhone 节点或账号地区解锁。'};out=root/a.json_out;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2));sys.exit(0 if ok else 1)
if __name__=='__main__':main()
