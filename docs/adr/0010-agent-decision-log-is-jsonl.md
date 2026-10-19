# The agent decision log is JSONL, checked by a schema

Agents record their run decisions in an append-only JSONL file, one object per line (ts, agent, phase, decision, why, evidence, result), validated by a JSON schema inside `just check`. A different model audits it at the end of a run, and `correct` mines it for repeated mistakes. Any vendored pstack text that names TSV is patched to JSONL, with the reason on the patch's first line. Pi sessions and the lane hand-off logs are JSONL too. Decided by Tom, 2026-10-18.

## Considered options

- TSV, as pstack's show-me-your-work and orchestrate playbook use. Rejected: free text in the why and evidence fields eventually contains a tab or newline and silently corrupts a row, and TSV has no types.
