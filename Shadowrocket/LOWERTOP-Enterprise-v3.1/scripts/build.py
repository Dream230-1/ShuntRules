#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import yaml


def deep_merge(base, overlay):
    if isinstance(base, dict) and isinstance(overlay, dict):
        result = dict(base)
        for key, value in overlay.items():
            result[key] = deep_merge(result[key], value) if key in result else value
        return result
    return overlay


def run(command, cwd):
    print('+', ' '.join(map(str, command)), flush=True)
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout, end='', flush=True)
    if result.stderr:
        print(result.stderr, end='', file=sys.stderr, flush=True)
    if result.returncode:
        raise RuntimeError(
            f'command failed ({result.returncode}): {command}\n'
            f'stdout:\n{result.stdout}\nstderr:\n{result.stderr}'
        )


def validate_generated(path: Path):
    text = path.read_text(encoding='utf-8')
    required = [
        'dns-fallback-system = false',
        'dns-direct-system = false',
        'dns-direct-fallback-proxy = false',
        'ipv6 = false',
        'prefer-ipv6 = false',
        'udp-policy-not-supported-behaviour = REJECT',
        'block-quic = always-allow',
        'FINAL,PROXY',
    ]
    errors = [f'missing: {item}' for item in required if item not in text]
    if '#proxy' not in next(
        (line for line in text.splitlines() if line.startswith('fallback-dns-server = ')), ''
    ):
        errors.append('fallback-dns-server missing #proxy')
    openai = text.find('DOMAIN-SUFFIX,openai.com,AI')
    advertising = text.find('AdvertisingLite')
    if openai < 0:
        errors.append('OpenAI AI rule missing')
    if advertising < 0:
        errors.append('AdvertisingLite ruleset missing')
    if openai >= 0 and advertising >= 0 and openai > advertising:
        errors.append('OpenAI rule must precede AdvertisingLite')
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--online', action='store_true')
    args = parser.parse_args()

    project = Path(__file__).resolve().parents[1]
    repo_root = project.parents[1]
    rc3 = repo_root / 'Shadowrocket' / 'LOWERTOP-Enterprise-v3.0-RC3'
    if not rc3.exists():
        raise SystemExit(f'RC3 build kernel not found: {rc3}')

    merged = yaml.safe_load((rc3 / 'manifest.yaml').read_text(encoding='utf-8'))
    for name in ('release.yaml', 'dns.yaml'):
        overlay = yaml.safe_load((project / 'config' / name).read_text(encoding='utf-8')) or {}
        merged = deep_merge(merged, overlay)

    features = yaml.safe_load((project / 'config' / 'features.yaml').read_text(encoding='utf-8')) or {}
    if not features.get('features', {}).get('advertising_lite', False):
        raise SystemExit('AdvertisingLite must remain enabled in v3.1 RC1')

    with tempfile.TemporaryDirectory(prefix='lowertop-v31-') as temp:
        workspace = Path(temp) / 'project'
        shutil.copytree(rc3, workspace)
        (workspace / 'manifest.yaml').write_text(
            yaml.safe_dump(merged, allow_unicode=True, sort_keys=False, width=180),
            encoding='utf-8',
        )

        run([sys.executable, 'scripts/generate.py', '--profile', 'all-release', '--mode', 'inline'], workspace)
        run([
            sys.executable, 'scripts/generate.py', '--profile', 'ipv6_svcb_experimental',
            '--mode', 'inline', '--out-dir', 'experimental'
        ], workspace)

        performance = workspace / 'build' / 'LOWERTOP-Enterprise-v3.1-RC1-Performance-Direct.conf'
        errors = validate_generated(performance)
        if errors:
            print(json.dumps({'ok': False, 'errors': errors}, ensure_ascii=False, indent=2))
            raise SystemExit(1)

        if args.online:
            print('online compatibility check: inherited RC3 kernel audits', flush=True)

        output = project / 'build'
        experimental = project / 'experimental'
        for directory in (output, experimental):
            if directory.exists():
                shutil.rmtree(directory)
            directory.mkdir(parents=True)

        for file in (workspace / 'build').glob('*'):
            if file.is_file():
                shutil.copy2(file, output / file.name)
        for file in (workspace / 'experimental').glob('*.conf'):
            shutil.copy2(file, experimental / file.name)

        summary = {
            'ok': True,
            'version': merged['meta']['version'],
            'kernel': 'LOWERTOP-Enterprise-v3.0-RC3',
            'online': args.online,
            'default_profile': features['features']['default_profile'],
            'outputs': sorted(file.name for file in output.glob('*.conf')),
            'experimental': sorted(file.name for file in experimental.glob('*.conf')),
            'dns_guard': 'passed',
            'advertising_lite': 'preserved',
        }
        (output / 'v31-build-summary.json').write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
