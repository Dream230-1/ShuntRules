\
#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import urlsplit
import argparse,json,re,sys
from common import artifact_label,load_yaml

def parse_general(path):
 d={};sec=None
 for raw in path.read_text(encoding='utf-8').splitlines():
  s=raw.strip()
  if not s or s.startswith('#'):continue
  if s.startswith('[') and s.endswith(']'):sec=s;continue
  if sec=='[General]' and '=' in s:k,v=s.split('=',1);d[k.strip()]=v.strip()
 return d
def csv(v):return [x.strip() for x in v.split(',') if x.strip()]
def pb(v):return {'true':True,'false':False}.get(str(v).lower())
def endpoint(x):return x.split('#',1)[0]
def fname(meta,p):return f'LOWERTOP-Enterprise-{artifact_label(meta)}-{p["title"]}-Direct.conf'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));ap.add_argument('--json-out',default='reports/dns-audit.json');a=ap.parse_args();root=Path(a.root).resolve();m=load_yaml(root/'manifest.yaml');pol=m['dns_audit'];results=[]
 for n,p in m['profiles'].items():
  directory='build' if p.get('release',True) else 'experimental';path=root/directory/fname(m['meta'],p);errors=[];warnings=[]
  if not path.exists():errors.append('生成配置不存在');cfg={}
  else:cfg=parse_general(path)
  for k in ['dns-server','fallback-dns-server','proxy-dns-server']:
   vals=csv(cfg.get(k,''))
   if not vals:errors.append(f'{k} 缺失')
   for x in vals:
    u=urlsplit(endpoint(x))
    if u.scheme!='https' or not u.netloc:errors.append(f'{k} 存在非 HTTPS DoH：{x}')
  for x in csv(cfg.get('fallback-dns-server','')):
   if '#proxy' not in x.lower():errors.append(f'境外备用 DNS 未经代理：{x}')
  for k in pol['required_false']:
   if pb(cfg.get(k)) is not False:errors.append(f'{k} 必须为 false')
  if n in pol['release_profiles']:
   if pb(cfg.get('ipv6')) is not False:errors.append('发布配置必须 ipv6=false')
  if n in pol['experimental_profiles']:
   if pb(cfg.get('ipv6')) is not True or pb(cfg.get('allow-dns-svcb')) is not True:errors.append('实验配置必须启用 IPv6 和 SVCB')
  if cfg.get('udp-policy-not-supported-behaviour')!='REJECT':errors.append('UDP 不支持时必须 REJECT')
  miss=[x for x in pol['required_hijack'] if x not in set(csv(cfg.get('hijack-dns','')))]
  if miss:errors.append(f'hijack-dns 缺少 {miss}')
  if cfg.get('block-quic')!=p['block-quic']:errors.append('QUIC 参数与 profile 不一致')
  results.append({'profile':n,'file':str(path.relative_to(root)),'ok':not errors,'errors':errors,'warnings':warnings})
 report={'ok':all(x['ok'] for x in results),'version':m['meta']['version'],'results':results,'scope_note':'静态检查不能替代真实 iPhone 的 DNSLeakTest、WebRTC、Wi-Fi 与蜂窝测试。'};out=root/a.json_out;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2));sys.exit(0 if report['ok'] else 1)
if __name__=='__main__':main()
