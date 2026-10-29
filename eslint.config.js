// The kit's own TypeScript (#245): templates/typescript's eslint config (typescript-eslint strict-type-checked and
// stylistic-type-checked). languages.json owns the tracked file set passed by check-ts, never a
// directory (eslint would walk into templates/, each with its own config).
import { defineConfig } from "eslint/config";
import tseslint from "typescript-eslint";

export default defineConfig(
  { ignores: ["node_modules"] },
  ...tseslint.configs.strictTypeChecked,
  ...tseslint.configs.stylisticTypeChecked,
  { languageOptions: { parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname } } },
);
