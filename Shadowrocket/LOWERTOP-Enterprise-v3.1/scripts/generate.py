\
#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path
from common import BUILTIN_POLICIES,artifact_label,load_yaml,parse_rule,read_rules,rule_key,rule_policy,sha256_file,upstream_url

def bv(v): return 'true' if v is True else 'false' if v is False else str(v)
def render_group(g):
    fields=[g['type'],*g.get('members',[]),*[f'{k}={v}' for k,v in g.get('params',{}).items()]]
    return f'{g["name"]} = '+','.join(map(str,fields))
def selected(m,r):
    if r=='all-release':return {k:v for k,v in m['profiles'].items() if v.get('release',True)}
    if r=='all':return m['profiles']
    return {r:m['profiles'][r]}
def validate_manifest(root,m):
    errors=[]; warnings=[]; groups={g['name'] for g in m['proxy_groups']}; valid=BUILTIN_POLICIES|groups
    if not re.fullmatch(r'[0-9a-f]{40}',m['meta']['upstream_commit']):errors.append('upstream_commit 必须为 40 位小写 SHA')
    seen={}
    for item in m['local_rulesets']:
        if item['policy'] not in valid:errors.append(f'{item["name"]} 引用未知策略')
        for ln,raw,p in read_rules(root/item['file']):
            key=rule_key(p); old=seen.get(key)
            if old and old['policy']!=item['policy']:errors.append(f'跨策略冲突 {key}: {old} / {item}')
            elif old:warnings.append(f'重复规则 {key}')
            else:seen[key]={'policy':item['policy'],'file':item['file'],'line':ln}
    for item in m['remote_rulesets']:
        if item['policy'] not in valid:errors.append(f'{item["name"]} 引用未知策略')
    for item in m['inline_rules']:
        p=parse_rule(item['rule']); pol=rule_policy(p)
        if pol and pol not in valid:errors.append(f'内联规则未知策略：{item["rule"]}')
    return errors,warnings

def render(root,m,pname,mode,base_url=None):
    p=m['profiles'][pname]; meta=m['meta']
    out=[f'# Shadowrocket Enterprise {artifact_label(meta)} - {p["title"]}',f'# Version: {meta["version"]}',f'# Generated: {meta["generated_date"]}','# Source: split YAML configuration',f'# Front rule mode: {mode}',f'# Upstream: {meta["upstream_repo"]}@{meta["upstream_commit"]}']
    out += [f'# {x}' for x in p.get('header_warnings',[])]
    out += ['# 请独立导入，不要与旧配置合并。','','[General]']
    general=dict(m['general_common']); general.update(p.get('general_overrides',{}))
    for k in ['skip-proxy','tun-excluded-routes']:out.append(f'{k} = {bv(general.pop(k))}')
    out += ['',f'dns-server = {p["dns-server"]}',f'fallback-dns-server = {p["fallback-dns-server"]}',f'proxy-dns-server = {p["proxy-dns-server"]}']
    out += [f'{k} = {bv(v)}' for k,v in general.items()]; out.append(f'block-quic = {p["block-quic"]}')
    out += ['','[Proxy]','# 节点由当前订阅提供。','','[Proxy Group]']+[render_group(g) for g in m['proxy_groups']]+['','[Rule]']
    entries=[]
    for x in m['inline_rules']:entries.append((x['stage'],'inline',x))
    for x in m['local_rulesets']:entries.append((x['stage'],'local',x))
    for x in m['remote_rulesets']:entries.append((x['stage'],'remote',x))
    for _,kind,item in sorted(entries,key=lambda x:x[0]):
        if kind=='inline':out += [f'# Inline: {item.get("comment",item["rule"])}',item['rule']]
        elif kind=='local':
            out.append(f'# Local ruleset: {item["name"]} → {item["policy"]}')
            if mode=='inline':out += [f'{raw},{item["policy"]}' for _ln,raw,_p in read_rules(root/item['file'])]
            else:
                if not base_url:raise ValueError('remote 模式需要 --base-url')
                out.append(f'RULE-SET,{base_url.rstrip("/")}/{item["file"]},{item["policy"]}')
        else:out += [f'# Remote ruleset: {item["name"]} → {item["policy"]}',f'RULE-SET,{upstream_url(m,item)},{item["policy"]}']
    out += [m['final_rule'],'','[Host]','localhost = 127.0.0.1','']
    return '\n'.join(out)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default=str(Path(__file__).resolve().parents[1])); ap.add_argument('--profile',default='all-release'); ap.add_argument('--mode',choices=['inline','remote'],default='inline'); ap.add_argument('--base-url'); ap.add_argument('--out-dir',default='build'); a=ap.parse_args()
    root=Path(a.root).resolve(); m=load_yaml(root/'manifest.yaml'); errors,warnings=validate_manifest(root,m)
    if errors: print(json.dumps({'ok':False,'errors':errors,'warnings':warnings},ensure_ascii=False,indent=2));sys.exit(1)
    od=root/a.out_dir;od.mkdir(parents=True,exist_ok=True);outputs=[]
    for n,p in selected(m,a.profile).items():
        txt=render(root,m,n,a.mode,a.base_url);suffix='Modular' if a.mode=='remote' else 'Direct';f=od/f'LOWERTOP-Enterprise-{artifact_label(m["meta"])}-{p["title"]}-{suffix}.conf';f.write_text(txt,encoding='utf-8');outputs.append({'profile':n,'file':str(f.relative_to(root)),'sha256':sha256_file(f)})
    report={'ok':True,'version':m['meta']['version'],'warnings':warnings,'outputs':outputs};(od/'audit-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
