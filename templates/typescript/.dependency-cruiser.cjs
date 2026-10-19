/** Architecture rules; `just check` fails on any violation. */
module.exports = {
  forbidden: [
    {
      name: "core-never-imports-cli",
      comment: "src/core.ts is the domain; only the CLI may depend on it, never the reverse.",
      severity: "error",
      from: { path: "^src/core" },
      to: { path: "^src/cli" },
    },
    { name: "no-circular", severity: "error", from: {}, to: { circular: true } },
  ],
  options: { tsConfig: { fileName: "tsconfig.json" }, doNotFollow: { path: "node_modules" } },
};
