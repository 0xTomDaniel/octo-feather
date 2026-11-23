// The git hook's rule (.githooks/pre-commit): the fast tier only for a writer's commit (octo-feather quality spec
// #acceptance-hook-machine-commit), else one line saying why it skipped. It cannot stop an agent whose environment
// lost OCTO_FEATHER_ROLE (taken for a maintainer), nor --no-verify.
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";

const writers = ["", "implementer", "corrector"]; // OCTO_FEATHER_ROLE unset: a maintainer
const inProgress = ["MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD"];

function skipped(): string | undefined {
  const role = process.env["OCTO_FEATHER_ROLE"] ?? "";
  if (!writers.includes(role)) return `OCTO_FEATHER_ROLE=${role}: a machine commit, not a writer's`;
  // One git call for the three paths; outside a repo it fails: no operation in progress.
  const p = spawnSync("git", ["rev-parse", ...inProgress.flatMap((h) => ["--git-path", h])], { encoding: "utf8" });
  const paths = p.status === 0 ? p.stdout.split("\n") : [];
  const head = inProgress.find((_, i) => paths[i] !== undefined && existsSync(paths[i]));
  return head === undefined ? undefined : `${head}: a merge, cherry-pick or revert in progress is a machine commit`;
}

const why = skipped();
if (why !== undefined) {
  process.stdout.write(`pre-commit: fast tier skipped: ${why}\n`);
  process.exit(0);
}
const run = spawnSync("just", ["fast"], { stdio: "inherit" });
process.exit(run.status ?? 1);
