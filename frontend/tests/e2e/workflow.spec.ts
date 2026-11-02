import { expect, test, type Page } from "@playwright/test";
import { MOCK_FAILURE_KEY, MOCK_STORAGE_KEY } from "../../src/lib/mock-transport";

const description = "Staff architecture role, cross-team collaboration, learning and international work. AI engineering preferred. Remote preferred; hybrid near Madrid at most two days. No frontend-only work. Good compensation.";
const browserErrors = new WeakMap<Page, string[]>();
test.beforeEach(async ({ page }) => {
  const errors: string[] = []; browserErrors.set(page, errors);
  page.on("pageerror", e => errors.push(e.message));
  page.on("console", message => { if (message.type() === "error") errors.push(message.text()); });
});
test.afterEach(async ({ page }) => { expect(browserErrors.get(page)).toEqual([]); });
async function step(page: Page, name: string) {
  await page.getByRole("navigation", { name: "Definition steps" }).getByRole("button", { name: new RegExp(name) }).click();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
}
async function start(page: Page, text = description) {
  await page.goto("/"); await page.getByRole("textbox", { name: "The role you’re looking for", exact: true }).fill(text);
  await page.getByRole("button", { name: "Save draft", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Definition saved");
}
async function failNext(page: Page, operation: string) { await page.evaluate(([key, value]) => sessionStorage.setItem(key, value), [MOCK_FAILURE_KEY, operation]); }
async function saved(page: Page) { return page.evaluate(key => JSON.parse(localStorage.getItem(key)!).definition, MOCK_STORAGE_KEY); }
const generate = (page: Page) => page.getByRole("button", { name: "Request clarification & suggestions", exact: true }).click();

test("full mocked journey: upload, review, answer states, save, reload, and refine", async ({ page }, info) => {
  test.setTimeout(60_000);
  const privateRequests: string[] = [];
  page.on("request", req => { if (new URL(req.url()).pathname.startsWith("/api/") || req.url().includes("api.openai.com")) privateRequests.push(req.url()); });
  await start(page);
  await page.screenshot({ path: info.outputPath("description.png"), fullPage: true });
  await step(page, "Background");
  await page.getByLabel("Document", { exact: true }).setInputFiles({ name: "synthetic-cv.md", mimeType: "text/markdown", buffer: Buffer.from("Built distributed systems.\nUsed SQL in a previous role.") });
  await page.getByRole("button", { name: "Add source", exact: true }).click();
  await page.getByRole("button", { name: "Suggest background facts", exact: true }).click();
  await expect(page.getByRole("blockquote").first()).toContainText("Built distributed systems");
  await page.getByLabel("Reviewed facts, one per line").fill("Led distributed systems architecture.\nPreviously used SQL; not a future requirement.");
  await page.getByRole("button", { name: "Accept reviewed facts", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Background facts accepted");
  await step(page, "Clarify"); await generate(page);
  const questions = page.locator(".question-card"); await expect(questions).toHaveCount(3);
  await questions.nth(0).getByRole("textbox").fill("Still deciding on compensation");
  await failNext(page, "answer");
  await questions.nth(0).getByRole("button", { name: "Save answer" }).click();
  await expect(page.getByRole("main").getByRole("alert")).toBeVisible();
  await expect(questions.nth(0).getByRole("textbox")).toHaveValue("Still deciding on compensation");
  await questions.nth(0).getByRole("button", { name: "Save answer" }).click();
  await questions.nth(1).getByRole("button", { name: "Skip question" }).click();
  await questions.nth(2).getByRole("button", { name: "I don’t know yet" }).click();
  await step(page, "Review & save");
  await expect(page.getByText("The suggestion context has changed", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Apply reviewed suggestions & save" })).toBeDisabled();
  await page.getByRole("button", { name: "Discard suggestions", exact: true }).click();
  await step(page, "Clarify"); await generate(page);
  await page.getByRole("button", { name: "Review suggested criteria", exact: true }).click();
  const salary = page.locator(".criterion").filter({ has: page.locator('input[value="salary"]') });
  const onsite = page.locator(".criterion").filter({ has: page.locator('input[value="onsite_limit"]') });
  await expect(salary.getByLabel("Value type")).toHaveValue("unknown");
  await expect(onsite.getByLabel("Maximum on-site days")).toHaveValue("2");
  await expect(onsite.getByLabel("On-site period")).toHaveValue("");
  await expect(onsite.getByLabel("Priority")).toHaveValue("mandatory");
  await page.getByRole("button", { name: "Apply reviewed suggestions & save" }).click();
  await expect(page.getByRole("status")).toContainText("Definition saved");
  expect((await saved(page)).preferences.some((p: { value: unknown }) => JSON.stringify(p.value).includes("SQL"))).toBe(false);
  await page.reload(); await expect(page.getByRole("textbox", { name: "The role you’re looking for", exact: true })).toHaveValue(description);
  await step(page, "Clarify");
  await expect(questions.nth(0).getByText("Answer saved", { exact: true })).toBeVisible();
  await expect(questions.nth(1).getByText("Skipped", { exact: true })).toBeVisible();
  await expect(questions.nth(2).getByText("Explicitly unknown", { exact: true })).toBeVisible();
  await step(page, "Background"); await page.getByRole("button", { name: "Review synthetic-cv.md", exact: true }).click();
  await expect(page.getByLabel("Reviewed facts, one per line")).toContainText("Led distributed systems architecture");
  await step(page, "Review & save");
  await salary.getByLabel("Value type").selectOption("compensation");
  await salary.getByLabel("Minimum", { exact: true }).fill("100000"); await salary.getByLabel("Maximum", { exact: true }).fill("120000");
  await salary.getByLabel("Currency").fill("eur"); await salary.getByLabel("Pay period").selectOption("year"); await salary.getByLabel("Tax basis").selectOption("gross");
  await onsite.getByLabel("On-site period").selectOption("week");
  await failNext(page, "save");
  await page.getByRole("button", { name: "Save definition", exact: true }).click();
  await expect(page.getByRole("main").getByRole("alert")).toBeInViewport();
  await expect(salary.getByLabel("Minimum", { exact: true })).toHaveValue("100000");
  await page.getByRole("button", { name: "Save definition", exact: true }).click(); await expect(page.getByRole("status")).toContainText("Definition saved");
  await page.screenshot({ path: info.outputPath("review.png"), fullPage: true });
  await page.reload(); await step(page, "Review & save");
  await expect(salary.getByLabel("Minimum", { exact: true })).toHaveValue("100000"); await expect(onsite.getByLabel("On-site period")).toHaveValue("week");
  await expect(page.getByLabel("Definition status")).toHaveCount(0);
  expect((await saved(page)).state).toBe("draft");
  expect(privateRequests).toEqual([]);
});

test("save and AI errors preserve edits and allow recovery", async ({ page }) => {
  await start(page, "A role I enjoy");
  await page.getByRole("textbox", { name: "The role you’re looking for", exact: true }).fill("Un puesto con equilibrio y aprendizaje"); await failNext(page, "save");
  await page.getByRole("button", { name: "Save draft", exact: true }).click(); await expect(page.getByRole("main").getByRole("alert")).toContainText("Try again");
  await expect(page.getByRole("textbox", { name: "The role you’re looking for", exact: true })).toHaveValue("Un puesto con equilibrio y aprendizaje");
  expect((await saved(page)).description).toBe("A role I enjoy");
  await page.getByRole("button", { name: "Save draft", exact: true }).click(); await expect(page.getByRole("status")).toContainText("Definition saved");
  await step(page, "Clarify"); await page.getByLabel("Assistance language").selectOption("Spanish"); await failNext(page, "ai"); await generate(page);
  await expect(page.getByRole("main").getByRole("alert")).toContainText("assistant is unavailable");
  await generate(page); await expect(page.locator(".question-card").first()).toContainText("rango salarial");
});

test("upload failures, unavailable links, and fact-review errors retain input", async ({ page }) => {
  await start(page); await step(page, "Background");
  await page.getByLabel("Document", { exact: true }).setInputFiles({ name: "cv.exe", mimeType: "application/octet-stream", buffer: Buffer.from("x") });
  await page.getByRole("button", { name: "Add source", exact: true }).click(); await expect(page.getByRole("main").getByRole("alert")).toContainText("Choose a PDF");
  await expect(page.getByLabel("Document", { exact: true })).toHaveValue(/cv.exe/);
  await page.getByLabel("Source type").selectOption("url"); await page.getByLabel("Source name").fill("Restricted profile"); await page.getByLabel("Public URL").fill("https://www.linkedin.com/in/example");
  await page.getByRole("button", { name: "Add source", exact: true }).click();
  await expect(page.getByText("Extraction failed", { exact: true })).toBeVisible(); await expect(page.getByText(/This page could not be retrieved/)).toBeVisible();
  await page.getByRole("button", { name: "Retry extraction", exact: true }).click(); await expect(page.getByRole("status")).toContainText("Extraction retried");
  await page.getByLabel("Source type").selectOption("text"); await page.getByLabel("Source name").fill("Pasted profile"); await page.getByLabel("Background text").fill("Experiencia previa con sistemas distribuidos.");
  await failNext(page, "upload"); await page.getByRole("button", { name: "Add source", exact: true }).click(); await expect(page.getByRole("main").getByRole("alert")).toBeVisible();
  await expect(page.getByLabel("Background text")).toHaveValue("Experiencia previa con sistemas distribuidos.");
  await page.getByRole("button", { name: "Add source", exact: true }).click();
  await page.getByLabel("Reviewed facts, one per line").fill("He diseñado sistemas distribuidos."); await failNext(page, "source-review");
  await page.getByRole("button", { name: "Accept reviewed facts", exact: true }).click(); await expect(page.getByRole("main").getByRole("alert")).toBeVisible();
  await expect(page.getByLabel("Reviewed facts, one per line")).toHaveValue("He diseñado sistemas distribuidos.");
  await page.getByRole("button", { name: "Accept reviewed facts", exact: true }).click(); await expect(page.getByRole("status")).toContainText("Background facts accepted");
});

test("manual criteria validate, preserve all value types, and survive refinement", async ({ page }) => {
  await page.goto("/"); await page.getByRole("button", { name: "Save draft", exact: true }).click(); await expect(page.getByRole("main").getByRole("alert")).toContainText("Enter a description");
  await page.getByRole("textbox", { name: "The role you’re looking for", exact: true }).fill("An incomplete draft"); await page.getByRole("button", { name: "Save draft", exact: true }).click();
  await step(page, "Review & save"); await page.getByRole("button", { name: "+ Add criterion", exact: true }).click();
  const criterion = page.locator(".criterion").first(); await criterion.getByLabel("Criterion name").fill("salary"); await criterion.getByLabel("Category").selectOption("compensation"); await criterion.getByLabel("Value type").selectOption("compensation");
  await criterion.getByLabel("Minimum", { exact: true }).fill("120000"); await criterion.getByLabel("Maximum", { exact: true }).fill("100000");
  await page.getByRole("button", { name: "Save definition", exact: true }).click(); await expect(page.getByRole("main").getByRole("alert")).toContainText("Minimum compensation");
  await expect(criterion.getByLabel("Minimum", { exact: true })).toHaveValue("120000");
  await criterion.getByLabel("Maximum", { exact: true }).fill("130000");
  for (const [key, type, value] of [["role", "string", "Architecture"], ["remote", "boolean", "false"], ["hours", "number", "32"], ["interests", "list", "AI\nSystems"]]) {
    await page.getByRole("button", { name: "+ Add criterion", exact: true }).click(); const row = page.locator(".criterion").last(); await row.getByLabel("Criterion name").fill(key); await row.getByLabel("Value type").selectOption(type);
    if (type === "boolean") await row.getByRole("combobox", { name: "Value", exact: true }).selectOption(value); else await row.getByLabel(type === "list" ? "Values, one per line" : "Value", { exact: true }).fill(value);
  }
  await page.getByRole("button", { name: "Save definition", exact: true }).click(); await expect(page.getByRole("status")).toContainText("Definition saved");
  await page.reload(); await step(page, "Review & save"); expect((await saved(page)).preferences.map((p: { value: unknown }) => p.value)).toEqual([expect.objectContaining({ minimum: 120000, maximum: 130000, currency: null, period: null, basis: null }), "Architecture", false, 32, ["AI", "Systems"]]);
  await page.getByRole("button", { name: "Remove criterion 2", exact: true }).click(); await page.getByRole("button", { name: "Save definition", exact: true }).click(); await expect(page.getByRole("status")).toContainText("Definition saved"); expect((await saved(page)).preferences).toHaveLength(4);
});

test("source and whole-definition deletion explain effects and clear derived context", async ({ page }) => {
  await start(page); await step(page, "Background");
  await page.getByLabel("Document", { exact: true }).setInputFiles({ name: "cv.md", mimeType: "text/markdown", buffer: Buffer.from("Historical experience.") }); await page.getByRole("button", { name: "Add source", exact: true }).click();
  await step(page, "Clarify"); await generate(page); await step(page, "Review & save"); await page.getByRole("button", { name: "Apply reviewed suggestions & save" }).click(); await expect(page.getByRole("status")).toContainText("Definition saved");
  const before = (await saved(page)).preferences;
  await step(page, "Background"); await page.getByRole("button", { name: "Remove cv.md", exact: true }).click(); await expect(page.getByText(/clears all clarification questions, answers, and conversation/)).toBeVisible(); await page.getByRole("button", { name: "Confirm remove source" }).click(); await expect(page.getByRole("status")).toContainText("Source removed");
  expect((await saved(page)).preferences).toEqual(before); expect((await saved(page)).clarifications).toEqual([]);
  await step(page, "Review & save"); await page.getByText("Delete this definition", { exact: true }).click(); await page.getByRole("button", { name: "Delete definition and sources", exact: true }).click(); await page.getByRole("button", { name: "Confirm delete definition", exact: true }).click(); await expect(page.getByRole("textbox", { name: "The role you’re looking for", exact: true })).toHaveValue(""); expect(await saved(page)).toBeNull();
});

test("keyboard step navigation preserves unfinished source input and guards unsaved reloads", async ({ page }) => {
  await start(page); const background = page.getByRole("navigation", { name: "Definition steps" }).getByRole("button", { name: /Background/ }); await background.focus(); await page.keyboard.press("Enter");
  await page.getByLabel("Source type").selectOption("text"); await page.getByLabel("Source name").fill("Unfinished notes"); await page.getByLabel("Background text").fill("Keep this while I change steps.");
  await step(page, "Describe"); await step(page, "Background"); await expect(page.getByLabel("Background text")).toHaveValue("Keep this while I change steps.");
  await step(page, "Describe"); await page.getByRole("textbox", { name: "The role you’re looking for", exact: true }).fill("Unsaved refinement"); await expect(page.getByText("Unsaved changes", { exact: true }).first()).toBeVisible();
  page.once("dialog", dialog => dialog.dismiss()); await page.getByRole("button", { name: "Reopen saved definition" }).click(); await expect(page.getByRole("textbox", { name: "The role you’re looking for", exact: true })).toHaveValue("Unsaved refinement");
  page.once("dialog", dialog => dialog.accept()); await page.getByRole("button", { name: "Reopen saved definition" }).click(); await expect(page.getByRole("textbox", { name: "The role you’re looking for", exact: true })).toHaveValue(description);
});

test("unavailable browser storage shows a retry state and keeps the editor disabled", async ({ page }) => {
  await page.addInitScript(key => localStorage.setItem(key, "invalid-json"), MOCK_STORAGE_KEY);
  await page.goto("/");
  await expect(page.getByRole("main").getByRole("alert")).toContainText("Browser storage is unavailable");
  await expect(page.getByRole("textbox", { name: "The role you’re looking for", exact: true })).toBeDisabled();
  await page.evaluate(key => localStorage.removeItem(key), MOCK_STORAGE_KEY);
  await page.getByRole("button", { name: "Retry opening workspace" }).click();
  await expect(page.getByRole("textbox", { name: "The role you’re looking for", exact: true })).toBeEnabled();
  await expect(page.getByRole("status")).toHaveText("Ready.");
});
