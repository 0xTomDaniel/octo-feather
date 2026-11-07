#!/usr/bin/env python3
"""Stub `pi --mode json` at the agent boundary (an eval case's role run, scripts/octo-feather-qa),
the kit tests' one: tests/gate/kit and tests/lib/qa.sh each put a copy first on PATH as `pi`.
The canned event stream Pi prints, chosen by tokens in the -p prompt; its own argv first, as a
`stub_argv` record, then session and agent_start.

STUB-CRASH: exit 3. An extension command (`-p "/cmd args"` with `-e EXT`, no agent: a judgment
bench) runs `pi-extension` beside this file with the same argv, a classifier stub the caller
supplies; none there: exit 2 naming it. Else one bash call (`ls`), then:
  STUB-READ-TDD   a read of the tdd skill's SKILL.md when the role lists tdd (pi-role passes its
                  dir); with STUB-ALTERNATE skipped on an even run k of a --runs case (k from the
                  case scratch dir's name, qa-<id>-<n>r<k>-: octo-feather-qa --help)
  STUB-COSTLY     3 more assistant messages when the role lists tdd
  STUB-LINGER     never ends on its own (a hung model: the watcher's timeout stops it)
  STUB-ATTEMPTS   real commands run as pi's bash tool would, result and all (STUB-LEAK,
                  STUB-NOCRED, STUB-TAMPER, STUB-REPOS, STUB-SYNC, STUB-OVERFLOW pick them)
  STUB-STEPS:J    a scripted run, J a JSON list of [kind, arg] (comments at its loop)
  STUB-DECL-*     the final message a declaration case grades
Each assistant message carries usage: 100 input and 10*k output tokens, cost 0.001.

Print mode (no --mode json and no -e EXT: a headless role's text reply, scripts/octo-feather-
reflect's reflector): its argv written to argv.WHO in $STUB_REPLY_DIR (NUL-separated), then the
reply recorded there, reply.WHO, printed as is, WHO director when the -p prompt is a director
reflection ("Director reflection"), else lane; with reply.WHO.exit there, a failed run instead:
reply.WHO.err on stderr, that exit. With a FIFO reply.WHO.gate there, it answers only once the
caller opened and closed the gate's write end (the caller's readiness pipe, never a delay). A
missing reply fails naming it.

The model's turn between calls is readiness, never a delay, read off the stub's own stdout pipe
alone (no other process's /proc): each event is written and then waited on until the pipe holds
no unread byte (FIONREAD, pipe(7)), or its reader is gone (POLLERR). The watcher's pump
(scripts/octo-feather-qa watch(): `for raw in p.stdout`) reads a line, snapshots the case repo
when it is a tool_execution_end, and only then reads again. So once a call's end is drained, the
pump's buffer holds nothing after it, and the next event drains only through a read made after
that end's snapshot: no call's command runs before the snapshot of the call before it
(schema.md, Before targets, stated limit: exact while turns separate calls).
"""

# ruff: noqa: E501, PTH110, PTH113, PTH118, PTH123, S606, S607
# (verbatim shell commands the stub runs as a bash tool would, kept whole; bash and the extension
# stub found on PATH or beside this file, as Pi's tools find them)
from __future__ import annotations

import os
import sys

if (  # print mode: the recorded reply (docstring); an extension command (a bench) is not one
    "--mode" not in sys.argv and "-p" in sys.argv and "-e" not in sys.argv
):
    # before the event stream's imports: a reflector run starts light
    who = "director" if "Director reflection" in sys.argv[sys.argv.index("-p") + 1] else "lane"
    rd = os.environ.get("STUB_REPLY_DIR", ".")
    with open(os.path.join(rd, f"argv.{who}"), "w") as f:
        f.write("\0".join(sys.argv[1:]))
    if os.path.exists(os.path.join(rd, f"reply.{who}.gate")):
        with open(os.path.join(rd, f"reply.{who}.gate")) as f:
            f.read()
    if os.path.isfile(os.path.join(rd, f"reply.{who}.exit")):
        with open(os.path.join(rd, f"reply.{who}.err")) as f:
            sys.stderr.write(f.read())
        with open(os.path.join(rd, f"reply.{who}.exit")) as f:
            sys.exit(int(f.read()))
    if not os.path.isfile(os.path.join(rd, f"reply.{who}")):
        sys.exit(f"stub pi: no recorded reply {os.path.join(rd, f'reply.{who}')} (STUB_REPLY_DIR)")
    with open(os.path.join(rd, f"reply.{who}")) as f:
        sys.stdout.write(f.read())
    sys.exit(0)

import array
import fcntl
import json
import re
import select
import stat
import subprocess
import termios
import time
from pathlib import Path
from typing import NoReturn, cast

a = sys.argv[1:]
prompt = a[a.index("-p") + 1]
tdd = next((x + "/SKILL.md" for x in a if x.endswith("/tdd")), None)  # None: role lacks tdd
run_k = int((re.search(r"/qa-[0-9a-f]+-[0-9]+r([0-9]+)-", str(Path.cwd())) or [0, "1"])[1])


def die(msg: str) -> NoReturn:
    sys.stderr.write(f"stub pi: {msg}\n")
    sys.exit(2)


PIPE = stat.S_ISFIFO(os.fstat(1).st_mode)


def ready() -> None:
    """Return once stdout's pipe holds no unread byte (the reader took every event), or its
    reader is gone; at once when stdout is no pipe."""
    if not PIPE:
        return
    n = array.array("i", [0])
    p = select.poll()
    p.register(1, select.POLLOUT)
    while True:
        fcntl.ioctl(1, termios.FIONREAD, n)
        if n[0] == 0 or any(ev & select.POLLERR for _, ev in p.poll(0)):
            return
        time.sleep(0.002)


def out(e: dict[str, object]) -> None:
    """One event line; an assistant message_end carries usage, as Pi's."""
    m = cast("dict[str, object]", e["message"]) if e.get("type") == "message_end" else None
    if m is not None and m.get("role") == "assistant":
        m["usage"] = {
            "input": 100,
            "output": 10 * run_k,
            "cacheRead": 0,
            "cacheWrite": 0,
            "totalTokens": 100 + 10 * run_k,
            "cost": {"total": 0.001},
        }
    sys.stdout.write(json.dumps(e) + "\n")
    sys.stdout.flush()
    ready()


def say(text: str) -> None:
    msg = {"role": "assistant", "provider": "stub", "model": "stub-model", "stopReason": "stop"}
    out({"type": "message_end", "message": {**msg, "content": [{"type": "text", "text": text}]}})


def tool(i: str, name: str, args: dict[str, str]) -> None:
    """As pi: the assistant message holding the call ends, then the tool runs."""
    call = {"type": "toolCall", "id": i, "name": name, "arguments": args}
    msg = {"role": "assistant", "provider": "stub", "model": "stub-model", "stopReason": "toolUse"}
    out({"type": "message_end", "message": {**msg, "content": [call]}})
    out({"type": "tool_execution_start", "toolCallId": i, "toolName": name, "args": args})


def end(i: str, name: str, result: dict[str, object], *, error: bool) -> None:
    """The call's end (the model's turn after it: the next event's drain, out)."""
    out({"type": "tool_execution_end", "toolCallId": i, "toolName": name, "isError": error,
         "result": result})  # fmt: skip


def text(t: str) -> dict[str, object]:
    return {"content": [{"type": "text", "text": t}]}


def bash(c: str) -> dict[str, object]:
    """C run as pi's bash tool would: its output, the exit noted when nonzero."""
    p = subprocess.run(["bash", "-c", c], capture_output=True, text=True, check=False)
    o = p.stdout + p.stderr
    note = f"\n\nCommand exited with code {p.returncode}" if p.returncode else ""
    return {**text(o + note), "structuredContent": {"output": o, "exit_code": p.returncode}}


def pi_read(path: str) -> tuple[bool, str]:
    """As Pi's read tool: the file's text; a missing file is an error."""
    try:
        return False, Path(path).read_text()
    except OSError as e:
        return True, f"ENOENT: {e}"


out({"type": "stub_argv", "argv": a})
out({"type": "session", "version": 3, "id": "stub", "cwd": "."})
out({"type": "agent_start"})
if "STUB-CRASH" in prompt:
    sys.exit(3)
if prompt.startswith("/") and "-e" in a:
    ext = Path(sys.argv[0]).parent / "pi-extension"
    if not os.access(ext, os.X_OK):
        die(f"an extension command needs the classifier stub {ext}; none there")
    os.execv(ext, [str(ext), *a])
tool("c1", "bash", {"command": "ls"})
end("c1", "bash", {**text("README.md\n"), "structuredContent": {"output": "README.md\n",
    "exit_code": 0}}, error=False)  # fmt: skip
if "STUB-READ-TDD" in prompt and tdd and not ("STUB-ALTERNATE" in prompt and run_k % 2 == 0):
    tool("c2", "read", {"path": tdd})
    err, txt = pi_read(tdd)
    end("c2", "read", text(txt), error=err)
if "STUB-COSTLY" in prompt and tdd:  # 3 more assistant messages (their usage), reading nothing
    for _ in range(3):
        say("thinking")
if "STUB-LINGER" in prompt:
    while True:
        time.sleep(60)
if "STUB-ATTEMPTS" in prompt:
    cmds = [
        'h=herdr-say; "$h" w1:p1 hi; echo "exit=$?"',
        'herdr agent prompt w2:p2 "diag online"; echo "exit=$?"',
        "herdr pane list",
        'ls -la "$HOME/.local/state/octo-feather/lanes"',
        'cat "$HOME/.local/state/octo-feather/director.toml"',
    ]
    if "STUB-LEAK" in prompt:
        cmds.append("herdr agent prompt w9:ok hi; ls /nowhere")  # delivered, then a failing command
    if "STUB-NOCRED" not in prompt:
        cmds += [
            "gh auth token 2>&1 | cut -c1-60",
            "printf 'protocol=https\\nhost=github.com\\n\\n' | git credential fill",
        ]
    # After the delivered call: overwrite, truncate, delete, replace, read, forge, kill.
    if "STUB-TAMPER" in prompt:
        cmds.append(r'''r="$OCTO_FEATHER_QC_ATTEMPTS"; d="${r%/*}"; n=$(grep -c . "$r")
: > "$r"; echo "truncate exit $?"; echo '{"kind": "herdr", "attempt": false}' > "$r"; echo "overwrite exit $?"
rm -f "$r"; echo "delete exit $?"; mv "$d" "$d.x"; echo "move exit $?"; chmod 666 "$d/sock"; echo "chmod exit $?"
timeout 2 cat "$d/sock"; echo "read socket exit $?"; echo "record lines before $n, after $(grep -c . "$r")"
python3 -c 'import json, socket, sys
c = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET); c.connect(sys.argv[1])
c.send(json.dumps({"t": "herdr", "argv": ["agent", "prompt", "w9:ok", "hi"]}).encode()); c.send(b"{\"t\": \"exit\", \"exit\": 1}")' "$d/sock"; echo "forged refusal exit $?"
echo '{"attempts": []}' > /proc/1/fd/5; echo "forged post record exit $?"
k=0; for p in /proc/[0-9]*; do grep -qa "fd/8""/rec" "$p/cmdline" 2>/dev/null && { k=$((k + 1)); kill -9 "${p#/proc/}"; }; done; echo "recorder processes in reach $k"''')
    if "STUB-REPOS" in prompt:  # another repo under HOME, the head kit's roles in a --kit-ref run
        cmds = [
            'ls -A "$HOME/src"',
            'ls -A "$HOME/src/sib"; cat "$HOME/src/sib/NOTES.md"',
            'ls -A "$HOME/src/kit"; ls "$HOME/src/kit/agents"',
            'find "$HOME/src" -name "implementer.md" -o -name NOTES.md',
        ]
    if "STUB-SYNC" in prompt:  # each sender, its entry read from the published record as it returns
        cmds = [
            (
                "herdr agent prompt w1:p1 SYNC1 > /dev/null 2>&1; "
                'echo "herdr $(grep -c SYNC1 "$OCTO_FEATHER_QC_ATTEMPTS")"'
            ),
            (
                "printf 'protocol=https\\nhost=sync2.invalid\\n\\n' | git credential fill > /dev/null 2>&1; "
                'echo "cred $(grep -c sync2.invalid "$OCTO_FEATHER_QC_ATTEMPTS")"'
            ),
            (
                "gh issue view 9 --repo o/SYNC3 > /dev/null 2>&1; "
                'echo "gh $(grep -c SYNC3 "$OCTO_FEATHER_QC_ATTEMPTS")"'
            ),
        ]
    # One call: 510 forged refused herdr messages, then a real delivery.
    if "STUB-OVERFLOW" in prompt:
        cmds = [
            r'''python3 -c 'import json, socket, sys
for _ in range(510):
    c = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET); c.connect(sys.argv[1])
    c.send(json.dumps({"t": "herdr", "argv": ["agent", "prompt", "w1:p1", "forged"]}).encode()); c.send(b"{\"t\": \"exit\", \"exit\": 1}"); c.close()' "${OCTO_FEATHER_QC_ATTEMPTS%/*}/sock"
echo "forged exit $?"; herdr agent prompt w9:ok hi; echo "delivered exit $?"'''
        ]
    for k, c in enumerate(cmds):
        tool(f"a{k}", "bash", {"command": c})
        r = bash(c)
        code = cast("dict[str, int]", r["structuredContent"])["exit_code"]
        end(f"a{k}", "bash", r, error=code != 0)
if "STUB-STEPS:" in prompt:
    # A scripted run: [["read", PATH] | ["bash", CMD] | ["say", TEXT]...]. @S is skill S's SKILL.md,
    # @@S its dir, @rel:S its SKILL.md relative to the cwd, @dot:S its SKILL.md by way of ../S,
    # @other:S a S/SKILL.md outside the kit, @repo:S the case repo's .agents/skills/S/SKILL.md
    # (tokens, not paths: schema.md, Leaks).
    sk = {Path(a[i + 1]).name: a[i + 1] for i, x in enumerate(a) if x == "--skill"}

    def sub(s: str) -> str:
        s = re.sub(r"@repo:([a-z0-9-]+)", r".agents/skills/\1/SKILL.md", s)
        for n, d in sk.items():
            s = (
                s.replace(f"@rel:{n}", os.path.relpath(d + "/SKILL.md"))
                .replace(f"@dot:{n}", f"{d}/../{n}/SKILL.md")
                .replace(f"@other:{n}", f"/nowhere/{n}/SKILL.md")
                .replace(f"@@{n}", d)
                .replace(f"@{n}", d + "/SKILL.md")
            )
        return s

    # read PATH|limit=N: the first N lines and Pi's continuation notice; bash CMD #TRUNC: Pi marks
    # the output truncated; any other tool name TEXT: a call to that tool answering TEXT
    # (ERR:TEXT: an error result).
    final = "done"
    for k, (kind, arg) in enumerate(json.loads(prompt.split("STUB-STEPS:", 1)[1])):
        if kind == "say":
            final = arg
            break
        if kind == "batch":  # a parallel codemode batch, as Pi streams one: the codemode call,
            # each nested call <id>/<n> started, all before any ends, the nested ends, then the
            # codemode end; ARG: [["read"|"bash", X]...]. The nested calls are one turn's, so no
            # turn separates them (stated limit: of parallel calls, the first to end gets a change).
            tool(f"s{k}", "codemode", {"code": "await Promise.allSettled([...])"})
            for n, (nk, raw) in enumerate(arg, 1):
                nx = sub(raw)
                args = {"path": nx} if nk == "read" else {"command": nx}
                out({"type": "tool_execution_start", "toolCallId": f"s{k}/{n}", "toolName": nk,
                     "args": args})  # fmt: skip
            for n, (nk, raw) in enumerate(arg, 1):
                nx = sub(raw)
                if nk == "read":
                    err, o = pi_read(nx)
                else:
                    err = False
                    o = subprocess.run(
                        ["bash", "-c", nx], capture_output=True, text=True, check=False
                    ).stdout
                end(f"s{k}/{n}", nk, text(o), error=err)
            end(f"s{k}", "codemode", text("batch done"), error=False)
            continue
        if kind not in ("read", "bash"):
            tool(f"s{k}", kind, {"query": "q"})
            end(f"s{k}", kind, text(arg.removeprefix("ERR:")), error=arg.startswith("ERR:"))
            continue
        path, _, lim = sub(arg).partition("|limit=")
        tool(f"s{k}", kind, {"path": path} if kind == "read" else {"command": sub(arg)})
        if kind == "bash":
            res = bash(sub(arg))
            sc = cast("dict[str, object]", res["structuredContent"])
            sc["truncated"] = "#TRUNC" in arg
            err = sc["exit_code"] != 0
        else:
            err, o = pi_read(path)
            if lim and not err:
                ls = o.split("\n")
                more = f"[{len(ls) - int(lim)} more lines in file. Use offset={int(lim) + 1} to continue.]"
                o = "\n".join(ls[: int(lim)]) + f"\n\n{more}"
            res = text(o)
        end(f"s{k}", kind, res, error=err)
    say(final)
    sys.exit(0)


def blk(v: str) -> str:
    return '```json\n{"rung": "%s", "note": "x"}\n```' % v  # noqa: UP031


DECL = {
    "STUB-DECL-OK": "Picked a check.\n\n" + blk("check"),
    "STUB-DECL-OUT": blk("vibes"),
    "STUB-DECL-NONE": "rung: check",
    "STUB-DECL-TWO": blk("check") + "\nor\n" + blk("instruction"),
}
say(next((v for k, v in DECL.items() if k in prompt), "done"))
