// The gate's own collector of criterion-tagged tests (qc.toml `tags`, read by the octo-feather kit's `just qc`): writes
// every collected test carrying a criterion tag, by its case id, with its criterion ids, as one JSON object to the file
// OCTO_FEATHER_QC_TAGS names, running no test (Vitest's own collection, `vitest.collect`, not a static parse: a test
// made in a loop counts too). A file that fails to collect fails it: whether a criterion has a tagged test is never
// guessed. Copyable unchanged beside tests/qc-capture.ts.
import { writeFileSync } from "node:fs";
import { createVitest } from "vitest/node";
import { caseId, criteria } from "./qc-capture.ts";

const out = process.env["OCTO_FEATHER_QC_TAGS"];
if (out === undefined || out === "") throw new Error("OCTO_FEATHER_QC_TAGS is unset: name the file the tagged cases go to");
const vitest = await createVitest({ watch: false, reporters: [] });
try {
  const { testModules, unhandledErrors } = await vitest.collect(undefined, { staticParse: false });
  const failed = testModules.filter((m) => m.errors().length > 0).map((m) => m.moduleId);
  if (failed.length > 0 || unhandledErrors.length > 0) {
    throw new Error(`collecting the tests failed: ${[...failed, ...unhandledErrors.map(String)].join("; ")}`);
  }
  const tagged: Record<string, string[]> = {};
  for (const m of testModules) {
    for (const t of m.children.allTests()) {
      const ids = criteria(t.tags);
      if (ids.length > 0) tagged[caseId(vitest.config.root, t)] = ids;
    }
  }
  writeFileSync(out, JSON.stringify(tagged));
} finally {
  await vitest.close();
}
