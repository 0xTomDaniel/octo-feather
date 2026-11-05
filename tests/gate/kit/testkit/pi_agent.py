#!/usr/bin/env python3
"""Stub `pi --mode json` at the agent boundary (an eval case's role run, scripts/octo-feather-qa):
the canned event stream Pi prints, chosen by tokens in the -p prompt, as tests/lib/qa.sh's stub
pi answers them (the subset the kit tests here ask). Its own argv first, as a `stub_argv` record;
one bash call (`ls`); STUB-READ-TDD: a read of the tdd skill's SKILL.md when the role lists tdd
(pi-role passes its dir), skipped on an even run k of a --runs case with STUB-ALTERNATE (run k
from the case scratch dir's name: octo-feather-qa --help); STUB-COSTLY: 3 more assistant
messages when the role lists tdd. Each assistant message carries usage: 100 input and 10*k
output tokens, cost 0.001. Ends on an assistant `done`."""

import json
import re
import sys
import time
from pathlib import Path
from typing import cast

a = sys.argv[1:]
prompt = a[a.index("-p") + 1]
tdd = next((x + "/SKILL.md" for x in a if x.endswith("/tdd")), None)
run_k = int((re.search(r"/qa-[0-9a-f]+-[0-9]+r([0-9]+)-", str(Path.cwd())) or [0, "1"])[1])


def out(e: dict[str, object]) -> None:
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


def say(text: str, stop: str = "stop") -> None:
    msg = {"role": "assistant", "provider": "stub", "model": "stub-model", "stopReason": stop}
    out({"type": "message_end", "message": {**msg, "content": [{"type": "text", "text": text}]}})


def tool(i: str, name: str, args: dict[str, str], text: str, *, ok: bool) -> None:
    """As pi: the assistant message holding the call ends, the tool runs, its result ends."""
    call = {"type": "toolCall", "id": i, "name": name, "arguments": args}
    msg = {"role": "assistant", "provider": "stub", "model": "stub-model", "stopReason": "toolUse"}
    out({"type": "message_end", "message": {**msg, "content": [call]}})
    out({"type": "tool_execution_start", "toolCallId": i, "toolName": name, "args": args})
    res: dict[str, object] = {"content": [{"type": "text", "text": text}]}
    if name == "bash":
        res["structuredContent"] = {"output": text, "exit_code": 0}
    end = {"toolCallId": i, "toolName": name, "isError": not ok, "result": res}
    out({"type": "tool_execution_end", **end})


out({"type": "stub_argv", "argv": a})
out({"type": "session", "version": 3, "id": "stub", "cwd": "."})
out({"type": "agent_start"})
tool("c1", "bash", {"command": "ls"}, "README.md\n", ok=True)
time.sleep(0.5)  # the model's next turn: the watcher snapshots this call's end before the next
if "STUB-READ-TDD" in prompt and tdd and not ("STUB-ALTERNATE" in prompt and run_k % 2 == 0):
    try:
        ok, txt = True, Path(tdd).read_text()
    except OSError as e:
        ok, txt = False, f"ENOENT: {e}"
    tool("c2", "read", {"path": tdd}, txt, ok=ok)
if "STUB-COSTLY" in prompt and tdd:
    for _ in range(3):
        say("thinking")
say("done")
