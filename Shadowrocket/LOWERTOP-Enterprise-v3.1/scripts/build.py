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
    print('+', ' '.join(map(str, command)))
    subprocess.run(command, cwd=cwd, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--online', action='store_true')
    parser.add_argument('--source-ref', default='0' * 40)
    parser.add_argument('--repository', default='Dream230-1/ShuntRules')
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
        run([sys.executable, 'scripts/regression.py', '--offline'], workspace)
        run([sys.executable, 'scripts/dns_audit.py'], workspace)

        if args.online:
            run([sys.executable, 'scripts/remote_audit.py'], workspace)
            run([sys.executable, 'scripts/ruleset_drift.py'], workspace)
            run([sys.executable, 'scripts/regression.py', '--online'], workspace)
            run([sys.executable, 'scripts/adblock_collision.py'], workspace)
            run([
                sys.executable, 'scripts/service_health.py', '--allow-warnings', '--allow-failures'
            ], workspace)
            run([sys.executable, 'scripts/network_benchmark.py'], workspace)

        output = project / 'build'
        reports = project / 'reports'
        experimental = project / 'experimental'
        for directory in (output, reports, experimental):
            if directory.exists():
                shutil.rmtree(directory)
            directory.mkdir(parents=True)

        for file in (workspace / 'build').glob('*'):
            if file.is_file():
                shutil.copy2(file, output / file.name)
        for file in (workspace / 'reports').glob('*.json'):
            shutil.copy2(file, reports / file.name)
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
        }
        (output / 'v31-build-summary.json').write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
