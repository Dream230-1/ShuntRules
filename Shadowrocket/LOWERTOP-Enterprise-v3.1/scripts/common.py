\
from __future__ import annotations
from pathlib import Path
import hashlib, ipaddress, json, re, yaml

BUILTIN_POLICIES={'DIRECT','PROXY','REJECT','REJECT-DROP','REJECT-NO-DROP'}
ALLOWED_RULE_TYPES={'DOMAIN','DOMAIN-SUFFIX','DOMAIN-KEYWORD','DOMAIN-WILDCARD','IP-CIDR','IP-CIDR6','IP-ASN','USER-AGENT','URL-REGEX','RULE-SET','DOMAIN-SET','GEOIP','DST-PORT','SRC-PORT','PROTOCOL','FINAL'}

def deep_merge(dst, src):
    if isinstance(dst,dict) and isinstance(src,dict):
        out=dict(dst)
        for k,v in src.items(): out[k]=deep_merge(out[k],v) if k in out else v
        return out
    return src

def load_yaml(path: Path):
    data=yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    includes=data.pop('includes',[]) or []
    merged={}
    for rel in includes:
        merged=deep_merge(merged, load_yaml(path.parent/rel))
    return deep_merge(merged,data)

def parse_rule(line):
    s=line.strip()
    if not s or s.startswith('#'): return None
    parts=[p.strip() for p in s.split(',')]
    if parts[0] not in ALLOWED_RULE_TYPES: raise ValueError(f'未知规则类型：{parts[0]} | {line}')
    if len(parts)<2: raise ValueError(f'规则字段不足：{line}')
    return parts

def read_rules(path: Path):
    rows=[]
    for i,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
        p=parse_rule(line)
        if p: rows.append((i,line.strip(),p))
    return rows

def rule_policy(parts):
    if not parts: return None
    if parts[0]=='FINAL': return parts[1] if len(parts)>1 else None
    if parts[0] in {'RULE-SET','DOMAIN-SET'}: return parts[2] if len(parts)>2 else None
    if len(parts)<3: return None
    return parts[-2] if parts[-1]=='no-resolve' else parts[-1]

def rule_key(parts): return ('FINAL',) if parts[0]=='FINAL' else (parts[0].upper(),parts[1].lower())
def sha256_file(path):
    h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()
def upstream_url(manifest,item):
    m=manifest['meta']; return f'https://raw.githubusercontent.com/{m["upstream_repo"]}/{m["upstream_commit"]}/{item["path"]}'
def artifact_label(meta):
    v=str(meta.get('version','3.1.0')); m=re.fullmatch(r'(\d+)\.(\d+)\.(\d+)(?:-(.+))?',v)
    if not m:return 'v3.1'
    a,b,_c,s=m.groups(); return f'v{a}.{b}'+(('-'+s.upper()) if s else '')
def cache_name(item): return item['name']+'.list'

def domain_match(host, parts):
    typ,val=parts[0],parts[1].lower(); h=host.lower().rstrip('.')
    if typ=='DOMAIN': return h==val
    if typ=='DOMAIN-SUFFIX': return h==val or h.endswith('.'+val)
    if typ=='DOMAIN-KEYWORD': return val in h
    if typ=='DOMAIN-WILDCARD':
        pat='^'+re.escape(val).replace(r'\*','.*')+'$'; return bool(re.match(pat,h))
    return False

def ip_match(host, parts):
    try: ip=ipaddress.ip_address(host)
    except ValueError:return False
    if parts[0] not in {'IP-CIDR','IP-CIDR6'}:return False
    try:return ip in ipaddress.ip_network(parts[1],strict=False)
    except ValueError:return False
