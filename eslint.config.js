import js from "@eslint/js";
import globals from "globals";
export default [
  js.configs.recommended,
  {
    files: ["app/static/*.js"],
    languageOptions: { globals: globals.browser },
    rules: { eqeqeq: "error", "no-var": "error", "prefer-const": "error", "no-eval": "error" },
  },
];
