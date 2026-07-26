\
#!/usr/bin/env python3
from pathlib import Path
import argparse,collections,hashlib,json,sys
import requests
from common import cache_name,load_yaml,parse_rule,upstream_url

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));ap.add_argument('--json-out',default='reports/remote-audit.json');a=ap.parse_args();root=Path(a.root).resolve();m=load_yaml(root/'manifest.yaml');cache=root/'.cache/remote-rules';cache.mkdir(parents=True,exist_ok=True);meta_dir=cache/'.meta';meta_dir.mkdir(exist_ok=True);results=[]
 headers={'User-Agent':m.get('cache',{}).get('user_agent','LOWERTOP-Enterprise/3.1')}
 for item in m['remote_rulesets']:
  url=upstream_url(m,item);fn=cache/cache_name(item);mf=meta_dir/(item['name']+'.json');mh={}
  if mf.exists():
   try:mh=json.loads(mf.read_text(encoding='utf-8'))
   except Exception:mh={}
  req_headers=dict(headers)
  if mh.get('etag'):req_headers['If-None-Match']=mh['etag']
  if mh.get('last_modified'):req_headers['If-Modified-Since']=mh['last_modified']
  warnings=[];status=None;from_cache=False
  try:
   r=requests.get(url,headers=req_headers,timeout=m.get('cache',{}).get('timeout',30));status=r.status_code
   if status==304 and fn.exists():data=fn.read_bytes();from_cache=True
   else:r.raise_for_status();data=r.content;fn.write_bytes(data);mf.write_text(json.dumps({'etag':r.headers.get('ETag'),'last_modified':r.headers.get('Last-Modified'),'url':url},indent=2)+'\n',encoding='utf-8')
  except Exception as e:
   if fn.exists():data=fn.read_bytes();from_cache=True;warnings.append(f'下载失败，使用缓存：{e}')
   else:data=b'';warnings.append(str(e))
  counts=collections.Counter();invalid=[]
  for i,line in enumerate(data.decode('utf-8','replace').splitlines(),1):
   try:p=parse_rule(line)
   except Exception as e:invalid.append({'line':i,'error':str(e)});continue
   if p:counts[p[0]]+=1
  n=sum(counts.values());au=item['audit'];errors=[]
  if len(data)>au['max_bytes']:errors.append('文件过大')
  if not au['min_rules']<=n<=au['max_rules']:errors.append(f'规则数 {n} 超出区间')
  if invalid:errors.append(f'存在 {len(invalid)} 条无效规则')
  results.append({'name':item['name'],'url':url,'policy':item['policy'],'ok':not errors,'http_status':status,'from_cache':from_cache,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'rule_count':n,'rule_types':dict(counts),'invalid_lines':invalid[:20],'warnings':warnings,'errors':errors})
 report={'ok':all(x['ok'] for x in results),'version':m['meta']['version'],'upstream_commit':m['meta']['upstream_commit'],'results':results};out=root/a.json_out;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2));sys.exit(0 if report['ok'] else 1)
if __name__=='__main__':main()
