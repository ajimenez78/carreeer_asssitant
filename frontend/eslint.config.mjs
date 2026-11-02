import { defineConfig, globalIgnores } from "eslint/config";
import js from "@eslint/js";
import next from "@next/eslint-plugin-next";
import tseslint from "typescript-eslint";

export default defineConfig([
  js.configs.recommended,
  tseslint.configs.recommended,
  next.configs["core-web-vitals"],
  globalIgnores([".next/**", ".next-mock-tests/**", "out/**", "next-env.d.ts", "playwright-report/**", "test-results/**"]),
]);
