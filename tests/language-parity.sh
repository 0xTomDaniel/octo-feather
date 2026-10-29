#!/usr/bin/env bash
# The kit language checker (scripts/check-languages, which templates/python copies byte for byte) and
# its TypeScript port (templates/typescript/scripts/check-languages.ts) give the same verdict on the
# same real git fixture repos (#362): exit status, stdout and stderr, the binding invocation each
# requires (python3 scripts/check-languages, node scripts/check-languages.ts) being the only difference.
# Each verdict is also held to an expected literal here, so the two cannot drift together.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
KIT="$kit" python3 - <<'PY'
import copy
import json
import os
import pathlib
import shutil
import subprocess
import tempfile

kit = pathlib.Path(os.environ['KIT'])
PY_INV = 'python3 scripts/check-languages'
TS_INV = 'node scripts/check-languages.ts'
JUSTFILE = '''export GATE_RECIPES := "check-scripts"
check: check-tests
check-tests *args:
    @{inv} gate "$@"
check-scripts:
    @{inv} run check-scripts
'''
BASE = {
    'languages': {
        'python': {'extensions': ['.py'], 'shebangs': ['python'], 'tools': ['lister']},
        'shell': {'extensions': ['.sh'], 'shebangs': ['bash', 'sh'], 'tools': ['lister']},
    },
    'tools': {'lister': {'program': 'printf', 'argv': ['printf', 'ran %s\\n'], 'recipe': 'check-scripts', 'install': 'install printf'}},
    'exemptions': [{'path': 'vendor', 'reason': 'Pinned upstream copy.'}],
    'noncode_extensions': ['.md', '.json'],
    'noncode_paths': ['NOTES', 'justfile'],
    'executable_roots': ['bin'],
}
FILES = {
    'app.py': 'print(1)\n',
    'bin/hook': '#!/usr/bin/env bash\necho hi\n',
    'bin/tool': '#!/usr/bin/env -S python3.12 -u\nprint(2)\n',
    'lib.sh': 'echo lib\n',
    'README.md': '# r\n',
    'NOTES': 'notes\n',
    'vendor/x.go': 'package x\n',
}
OK_CHECK = 'languages: ok python=2, shell=2\n'
OK_RUN = 'ran app.py\nran bin/hook\nran bin/tool\nran lib.sh\n'


def unknown(name):
    return f'check-languages: {name}: unknown type; declare its language or reasoned exemption\n'


def altered(name, command):
    return f'check-languages: {name}: altered binding; use the complete invocation @{PY_INV} {command}\n'


def build(folder, inv, case):
    files = dict(FILES)
    files.update(case.get('add', {}))
    for name in case.get('remove', []):
        files.pop(name)
    for name, text in files.items():
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        if name.startswith('bin/') and name not in case.get('not_executable', []):
            path.chmod(0o755)
    declaration = copy.deepcopy(BASE)
    case.get('declare', lambda d: None)(declaration)
    (folder / 'languages.json').write_text(json.dumps(declaration))
    justfile = JUSTFILE.format(inv=inv)
    for old, new in case.get('justfile', []):
        assert old.format(inv=inv) in justfile, (old, justfile)
        justfile = justfile.replace(old.format(inv=inv), new.format(inv=inv))
    (folder / 'justfile').write_text(justfile)
    (folder / 'scripts').mkdir()
    for name in ('check-languages', 'language_support.py'):
        shutil.copy2(kit / 'scripts' / name, folder / 'scripts' / name)
    shutil.copy2(kit / 'templates/typescript/scripts/check-languages.ts', folder / 'scripts/check-languages.ts')
    subprocess.run(['git', 'init', '-q'], cwd=folder, check=True)
    subprocess.run(['git', 'add', '-A', '--', *files, 'languages.json', 'justfile'], cwd=folder, check=True)


def verdict(inv, case, command):
    with tempfile.TemporaryDirectory(prefix='parity-') as name:
        folder = pathlib.Path(name)
        build(folder, inv, case)
        argv = ['python3', 'scripts/check-languages'] if inv == PY_INV else ['node', 'scripts/check-languages.ts']
        result = subprocess.run([*argv, *command], cwd=folder, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr.replace(TS_INV, PY_INV)


def set_reason(reason):
    def apply(d):
        d['exemptions'][0]['reason'] = reason
    return apply


def set_argv(argv):
    def apply(d):
        d['tools']['lister']['argv'] = argv
    return apply


CASES = [
    ('clean', {}, [], (0, OK_CHECK, '')),
    ('clean run executes declared argv', {}, ['run', 'check-scripts'], (0, OK_RUN, '')),
    ('unknown type', {'add': {'main.go': 'package main\n'}}, [], (1, '', unknown('main.go'))),
    ('extensionless without shebang', {'add': {'bin/data': 'plain\n'}}, [], (1, '', unknown('bin/data'))),
    ('extensionless shebang of an undeclared interpreter', {'add': {'bin/r': '#!/usr/bin/env ruby\nputs 1\n'}}, [], (1, '', unknown('bin/r'))),
    ('uv run --script shebang is python', {'add': {'bin/u': '#!/usr/bin/env -S uv run --script\nprint(3)\n'}}, ['files', 'python'], (0, 'app.py\nbin/tool\nbin/u\n', '')),
    ('exemption without a reason', {'declare': set_reason('  ')}, [], (1, '', unknown('vendor/x.go'))),
    ('ambiguous', {'declare': lambda d: d['languages']['shell']['extensions'].append('.py')}, [], (1, '', 'check-languages: app.py: ambiguous language; fix declaration\n')),
    ('missing tool', {'declare': lambda d: d['languages']['shell']['tools'].append('shellcheck')}, [], (1, '', 'check-languages: shellcheck: missing tool; restore its executable declaration\n')),
    ('echo binding', {'justfile': [('    @{inv} run check-scripts', '    @echo {inv} run check-scripts')]}, [], (1, '', altered('check-scripts', 'run check-scripts'))),
    ('commented binding', {'justfile': [('    @{inv} run check-scripts', '    # {inv} run check-scripts')]}, [], (1, '', altered('check-scripts', 'run check-scripts'))),
    ('gate binding altered', {'justfile': [('    @{inv} gate "$@"', '    @{inv} gate')]}, [], (1, '', altered('check-tests', 'gate "$@"'))),
    ('unreachable recipe', {'justfile': [(':= "check-scripts"', ':= ""')]}, [], (1, '', 'check-languages: lister: bind check-scripts in the reachable gate\n')),
    ('check without check-tests', {'justfile': [('check: check-tests', 'check:')]}, [], (1, '', 'check-languages: check: restore the check-tests dependency\n')),
    ('argv not executing its program', {'declare': set_argv(['echo', 'printf'])}, [], (1, '', 'check-languages: lister: argv must execute declared program printf\n')),
    ('uv launcher accepted', {'declare': set_argv(['uv', 'run', '--locked', '--offline', '--no-sync', 'printf', 'x'])}, [], (0, OK_CHECK, '')),
    ('altered uv launcher', {'declare': set_argv(['uv', 'run', 'printf', 'x'])}, [], (1, '', 'check-languages: lister: argv must execute declared program printf\n')),
    ('pnpm launcher accepted', {'declare': set_argv(['pnpm', 'exec', 'printf', 'x'])}, [], (0, OK_CHECK, '')),
    ('not executable', {'not_executable': ['bin/hook']}, ['run', 'check-scripts'], (1, '', 'check-languages: not executable: bin/hook; chmod +x bin/hook\n')),
    ('missing program', {'declare': lambda d: d['tools']['lister'].update(program='nonesuch-w362', argv=['nonesuch-w362'])}, ['run', 'check-scripts'], (1, '', "check-languages: lister: [Errno 2] No such file or directory: 'nonesuch-w362'; install printf\n")),
]

bad = 0
for label, case, command, expected in CASES:
    python = verdict(PY_INV, case, command)
    port = verdict(TS_INV, case, command)
    if python != expected or port != expected:
        bad = 1
        print(f'parity: {label}: expected {expected!r}\n  kit checker {python!r}\n  TypeScript port {port!r}')
    else:
        print(f'parity: {label}: exit {expected[0]} agreed')
if bad:
    raise SystemExit('language-parity: fix the checker whose verdict differs (scripts/language_support.py or templates/typescript/scripts/check-languages.ts)')
print(f'language-parity: ok ({len(CASES)} fixture repos, identical verdicts)')
PY
