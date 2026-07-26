\
#!/usr/bin/env python3
from pathlib import Path
import argparse,json,re,shutil,subprocess,sys
from common import load_yaml,sha256_file

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));ap.add_argument('--source-ref',required=True);ap.add_argument('--repository',required=True);ap.add_argument('--out-dir',default='dist');a=ap.parse_args();root=Path(a.root).resolve();m=load_yaml(root/'manifest.yaml')
 if not re.fullmatch(r'[0-9a-f]{40}',a.source_ref):raise SystemExit('source-ref 必须为 40 位 SHA')
 base=f'https://raw.githubusercontent.com/{a.repository}/{a.source_ref}/{m["meta"]["project_path"]}'
 subprocess.run([sys.executable,str(root/'scripts/generate.py'),'--root',str(root),'--profile','all-release','--mode','inline'],check=True)
 subprocess.run([sys.executable,str(root/'scripts/generate.py'),'--root',str(root),'--profile','all-release','--mode','remote','--base-url',base,'--out-dir','build-modular'],check=True)
 subprocess.run([sys.executable,str(root/'scripts/generate.py'),'--root',str(root),'--profile','ipv6_svcb_experimental','--mode','inline','--out-dir','experimental'],check=True)
 out=root/a.out_dir/m['meta']['version']
 if out.exists():shutil.rmtree(out)
 for d in ['direct','modular','experimental','rules','reports']:(out/d).mkdir(parents=True,exist_ok=True)
 for f in (root/'build').glob('*.conf'):shutil.copy2(f,out/'direct'/f.name)
 for f in (root/'build-modular').glob('*.conf'):shutil.copy2(f,out/'modular'/f.name)
 for f in (root/'experimental').glob('*.conf'):shutil.copy2(f,out/'experimental'/f.name)
 for item in m['local_rulesets']:
  src=root/item['file'];dst=out/'rules'/item['file'].replace('/','__');shutil.copy2(src,dst)
 for f in (root/'reports').glob('*.json'):shutil.copy2(f,out/'reports'/f.name)
 for f in ['manifest.yaml','README.md','CHANGELOG.md','TEST-MATRIX.md']:
  if (root/f).exists():shutil.copy2(root/f,out/f)
 files=sorted(p for p in out.rglob('*') if p.is_file());(out/'CHECKSUMS.sha256').write_text(''.join(f'{sha256_file(p)}  {p.relative_to(out).as_posix()}\n' for p in files),encoding='utf-8')
 rel={'version':m['meta']['version'],'source_ref':a.source_ref,'repository':a.repository,'recommended':next((p.name for p in (out/'direct').glob('*Performance*.conf')),None),'dns_leak_guard':True,'adblock':'AdvertisingLite'};(out/'release.json').write_text(json.dumps(rel,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(rel,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
