import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["eslint.config.js", ".dependency-cruiser.cjs", "node_modules"] },
  ...tseslint.configs.strictTypeChecked,
  ...tseslint.configs.stylisticTypeChecked,
  { languageOptions: { parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname } } },
);
