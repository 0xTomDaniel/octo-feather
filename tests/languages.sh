#!/usr/bin/env bash
# Public declaration dispatch and mutations in a scratch target; no live gate or model job.
set -euo pipefail
python3 - <<'PY'
import copy
import json
import pathlib
import shutil
import subprocess
import tempfile

root = pathlib.Path.cwd()
with tempfile.TemporaryDirectory(prefix='languages-') as folder:
    target = pathlib.Path(folder)
    (target / 'scripts').mkdir()
    (target / 'tests/gate').mkdir(parents=True)
    for name in ('check-languages', 'language_support.py'):
        shutil.copy2(root / 'scripts' / name, target / 'scripts' / name)
    for name in ('pyproject.toml', 'uv.lock'):
        shutil.copy2(root / name, target / name)
    shutil.copy2(root / 'tests/gate/test_gate.py', target / 'tests/gate/test_gate.py')
    (target / 'probe.py').write_text('print("probe")\n')
    (target / 'record.py').write_text('import json, pathlib, sys\npathlib.Path("invoked.json").write_text(json.dumps(sys.argv))\n')
    justfile = '''export GATE_RECIPES := "check-probe"
check: check-tests
check-tests *args:
    @python3 scripts/check-languages gate "$@"
check-probe:
    @python3 scripts/check-languages run check-probe
'''
    declaration = {
        'languages': {'python': {'extensions': ['.py'], 'shebangs': [], 'tools': ['recorder']}},
        'tools': {'recorder': {'program': 'python3', 'recipe': 'check-probe', 'argv': ['python3', 'record.py', '--required-argument'], 'install': 'install Python3'}},
        'noncode_extensions': [], 'noncode_paths': [], 'exemptions': []}
    def reset():
        (target / 'justfile').write_text(justfile)
        (target / 'languages.json').write_text(json.dumps(declaration))
    def run(*command):
        result = subprocess.run(command, cwd=target, capture_output=True, text=True)
        print('$', *command, '\n', result.stdout, result.stderr, 'exit=', result.returncode)
        return result
    reset()
    assert run('git', 'init', '-q').returncode == 0
    assert run('git', 'add', 'probe.py').returncode == 0
    assert run('just', 'check').returncode == 0
    invoked = json.loads((target / 'invoked.json').read_text())
    assert invoked == ['record.py', '--required-argument', 'probe.py'], invoked
    print('ACTUALLY INVOKED', invoked)
    def refused(label, text):
        result = run('python3', 'scripts/check-languages')
        assert result.returncode != 0 and text in result.stderr, (label, result)
        print(label, 'REJECTED')
        reset()
    for label, replacement in [('echo', '@echo python3 scripts/check-languages run check-probe'), ('comment', '# python3 scripts/check-languages run check-probe'), ('altered binding', '@python3 scripts/check-languages run check-probe extra')]:
        (target / 'justfile').write_text(justfile.replace('@python3 scripts/check-languages run check-probe', replacement))
        refused(label, 'altered binding')
    (target / 'justfile').write_text(justfile.replace(':= "check-probe"', ':= ""'))
    refused('unreachable recipe', 'reachable gate')
    mutation = copy.deepcopy(declaration)
    del mutation['tools']['recorder']
    (target / 'languages.json').write_text(json.dumps(mutation))
    refused('missing tool', 'missing tool')
    mutation = copy.deepcopy(declaration)
    mutation['tools']['recorder']['argv'] = ['echo', 'python3']
    (target / 'languages.json').write_text(json.dumps(mutation))
    refused('nonexecuting argv', 'argv must execute')
    (target / 'unknown.go').write_text('package main\n')
    assert run('git', 'add', 'unknown.go').returncode == 0
    refused('unknown language', 'unknown.go: unknown type')
print('languages: public dispatch and mutations passed')
PY
