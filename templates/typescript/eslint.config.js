import { defineConfig } from "eslint/config";
import tseslint from "typescript-eslint";

export default defineConfig(
  { ignores: ["node_modules"] },
  ...tseslint.configs.strictTypeChecked,
  ...tseslint.configs.stylisticTypeChecked,
  { languageOptions: { parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname } } },
);
