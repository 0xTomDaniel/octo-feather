#!/usr/bin/env bash
# Public install-check rejects a changed native-tool pin with its installation fix.
set -euo pipefail
uv run --locked --offline --no-sync python - <<'PY'
import pathlib
import os
import subprocess
import shutil
import tempfile
import yaml

root = pathlib.Path.cwd()
with tempfile.TemporaryDirectory() as folder:
    copy = pathlib.Path(folder)
    paths = subprocess.check_output(['git', 'ls-files', '-z'], text=True).split('\0')
    for name in filter(None, paths):
        dest = copy / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / name, dest)
    for name in ('.venv', 'node_modules'):
        (copy / name).symlink_to(root / name, target_is_directory=True)
    # Non-gate host integrations stay offline; the native gate tools and package metadata are real.
    bin_dir = copy / 'bin'
    bin_dir.mkdir()
    for name, body in {'gh': 'exit 0', 'herdr': 'exit 0', 'agent-browser': 'echo agent-browser ' + (root / 'agent-browser-version').read_text().strip()}.items():
        path = bin_dir / name
        path.write_text('#!/bin/sh\n' + body + '\n')
        path.chmod(0o755)
    env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ['PATH'])
    command = ['just', '--justfile', str(copy / 'justfile'), 'install-check', str(root)]
    clean = subprocess.run(command, env=env, capture_output=True, text=True)
    assert clean.returncode == 0, clean.stdout + clean.stderr
    (copy / 'node-version').write_text('0.0.1\n')
    result = subprocess.run(command, env=env, capture_output=True, text=True)
    output = result.stdout + result.stderr
    assert result.returncode != 0, output
    assert 'node' in output and 'WRONG VERSION' in output and 'node-version' in output, output
    assert 'https://nodejs.org/dist/v0.0.1/' in output, output
    (copy / 'node-version').write_text((root / 'node-version').read_text())
    lock = copy / 'pnpm-lock.yaml'
    data = yaml.safe_load(lock.read_text())
    resolved = str(data['importers']['.']['devDependencies']['typescript']['version']).split('(', 1)[0]
    # Mutate the resolved importer version only; the manifest's range remains unchanged.
    data['importers']['.']['devDependencies']['typescript']['version'] = '0.0.1'
    lock.write_text(yaml.safe_dump(data))
    result = subprocess.run(command, env=env, capture_output=True, text=True)
    output = result.stdout + result.stderr
    assert result.returncode != 0, output
    assert f'typescript WRONG VERSION {resolved}, want 0.0.1 (pnpm-lock.yaml)' in output, output
    assert 'pnpm install --frozen-lockfile' in output, output
print('tool-pins: real clean native dependencies pass; edited node pin and resolved TS lock rejected')
PY
