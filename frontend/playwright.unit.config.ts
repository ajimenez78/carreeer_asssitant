import { defineConfig } from "@playwright/test";
export default defineConfig({ testDir: "./tests/unit", outputDir: "./test-results/unit", forbidOnly: Boolean(process.env.CI) });
