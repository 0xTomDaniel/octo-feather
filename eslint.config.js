// The kit's own TypeScript (#245): templates/typescript's eslint config (typescript-eslint strict-type-checked and
// stylistic-type-checked). Which files: just check-ts passes the files tsc lists for tsconfig.json, the one
// declaration of the set, never a directory (eslint would walk into templates/, each with its own config).
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["eslint.config.js", "node_modules"] },
  ...tseslint.configs.strictTypeChecked,
  ...tseslint.configs.stylisticTypeChecked,
  { languageOptions: { parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname } } },
);
