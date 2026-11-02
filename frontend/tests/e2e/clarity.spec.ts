import { expect, test, type Page } from "@playwright/test";
import { MOCK_AI_DELAY_KEY, MOCK_FAILURE_KEY, MOCK_STORAGE_KEY } from "../../src/lib/mock-transport";

const current = (page: Page) => page.evaluate(key => JSON.parse(localStorage.getItem(key)!).definition, MOCK_STORAGE_KEY);
const step = (page: Page, name: RegExp) => page.locator(".sidebar nav").getByRole("button", { name }).click();
const evaluate = (page: Page) => page.getByRole("button", { name: "Assess clarity & update summary", exact: true }).click();
async function start(page: Page, text: string) {
  await page.goto("/");
  await page.getByRole("textbox", { name: "The role you’re looking for", exact: true }).fill(text);
  await page.getByRole("button", { name: "Save draft", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Definition saved");
}
async function checkNoOverflow(page: Page) { expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true); }

test("system evaluates clarity and the summary shows saved content across reloads and languages", async ({ page }, info) => {
  const errors: string[] = []; page.on("pageerror", e => errors.push(e.message));
  const description = "Staff architect designing distributed systems, remote in Spain. Salary is flexible.";
  await start(page, description);
  await step(page, /Summary/);
  await expect(page.getByText("Your saved definition needs a current assessment before its summary can be shown. Request one when you want to continue.")).toBeVisible();
  await evaluate(page);
  const summary = page.getByRole("article", { name: "Saved role summary", exact: true });
  await expect(summary).toContainText("Sufficiently clear");
  await expect(summary).toContainText(description);
  expect((await current(page)).state).toBe("ready");
  expect((await current(page)).preferences).toEqual([]);
  await expect(page.getByText("This view describes your saved definition. Unsaved edits and proposed criteria are not included until you review and save them.")).toBeVisible();
  await page.locator(".locale-switcher select").selectOption("es");
  await expect(page.getByRole("article", { name: "Resumen del puesto guardado", exact: true })).toContainText(description);
  await expect(page.getByRole("article", { name: "Resumen del puesto guardado", exact: true })).toContainText("Suficientemente clara");
  await checkNoOverflow(page);
  page.once("dialog", d => d.accept());
  await page.reload();
  await step(page, /Resumen/);
  await expect(page.getByRole("article", { name: "Resumen del puesto guardado", exact: true })).toContainText(description);
  await page.screenshot({ path: info.outputPath("role-summary.png"), fullPage: true });
  await page.locator(".locale-switcher select").selectOption("en");
  await step(page, /Describe/);
  await page.getByRole("textbox", { name: "The role you’re looking for", exact: true }).fill("A new direction that is still vague");
  await step(page, /Summary/);
  await expect(summary).toContainText(description);
  await expect(summary).not.toContainText("A new direction");
  await step(page, /Describe/); await page.getByRole("button", { name: "Save draft", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Definition saved");
  await step(page, /Summary/); await expect(summary).toHaveCount(0);
  await evaluate(page);
  await expect(summary).toContainText("Needs clarification");
  await expect(page.getByRole("heading", { name: "Still to clarify", exact: true })).toBeVisible();
  await expect(page.getByLabel("Definition status")).toHaveCount(0);
  expect(errors).toEqual([]);
});

test("stop cancels in-flight assessment, preserves typed answers, and persists until explicit resume", async ({ page }) => {
  await start(page, "A role I enjoy"); await step(page, /Summary/); await evaluate(page);
  await step(page, /Review & save/); await page.getByRole("button", { name: "Discard suggestions", exact: true }).click();
  await step(page, /Clarify/);
  const answer = page.locator(".question-card").first().getByRole("textbox");
  await answer.fill("My unfinished answer is preserved.");
  await page.evaluate(key => sessionStorage.setItem(key, "2000"), MOCK_AI_DELAY_KEY);
  await page.getByRole("button", { name: "Request clarification & suggestions", exact: true }).click();
  await expect(page.getByRole("button", { name: "Stop clarification", exact: true })).toBeEnabled();
  await page.getByRole("button", { name: "Stop clarification", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Clarification stopped.");
  await expect(answer).toHaveValue("My unfinished answer is preserved.");
  const paused = await current(page); expect(paused.clarification_paused).toBe(true);
  expect(paused.clarifications).toHaveLength(3);
  await expect(page.getByRole("button", { name: "Request clarification & suggestions", exact: true })).toBeDisabled();
  await step(page, /Background/);
  await page.getByLabel("Source type").selectOption("text"); await page.getByLabel("Source name").fill("Unfinished source"); await page.getByLabel("Background text").fill("Still being written.");
  await page.getByRole("button", { name: "Resume clarification", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Clarification resumed.");
  await expect(page.getByLabel("Background text")).toHaveValue("Still being written.");
  await page.getByRole("button", { name: "Stop clarification", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Clarification stopped.");
  await page.reload(); await step(page, /Summary/);
  await expect(page.getByRole("button", { name: "Resume clarification", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Assess clarity & update summary", exact: true })).toBeDisabled();
  const before = await current(page);
  await page.getByRole("button", { name: "Resume clarification", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Clarification resumed.");
  expect((await current(page)).assessment).toEqual(before.assessment);
  expect((await current(page)).clarifications).toEqual(before.clarifications);
});

test("failed stop persistence reports unsaved choice and can retry without losing input", async ({ page }) => {
  await start(page, "A role I enjoy");
  await page.getByRole("textbox", { name: "The role you’re looking for", exact: true }).fill("Unsaved preference text");
  await page.evaluate(key => sessionStorage.setItem(key, "control"), MOCK_FAILURE_KEY);
  await page.getByRole("button", { name: "Stop clarification", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("stopping could not be saved");
  expect((await current(page)).clarification_paused).toBe(false);
  await expect(page.getByRole("textbox", { name: "The role you’re looking for", exact: true })).toHaveValue("Unsaved preference text");
  await page.getByRole("button", { name: "Retry stopping", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Clarification stopped.");
  expect((await current(page)).clarification_paused).toBe(true);
  await expect(page.getByRole("textbox", { name: "The role you’re looking for", exact: true })).toHaveValue("Unsaved preference text");
});

test("new source and answer actions invalidate summary and obsolete clarification cards", async ({ page }) => {
  await start(page, "A role I enjoy"); await step(page, /Summary/); await evaluate(page);
  await step(page, /Review & save/); await page.getByRole("button", { name: "Discard suggestions", exact: true }).click();
  await step(page, /Clarify/);
  await page.locator(".question-card").first().getByRole("button", { name: "I don’t know yet", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Answer marked unknown");
  expect((await current(page)).assessment).toBeNull();
  await step(page, /Summary/); await evaluate(page);
  await step(page, /Review & save/); await page.getByRole("button", { name: "Discard suggestions", exact: true }).click();
  await step(page, /Background/); await page.getByLabel("Source type").selectOption("text");
  await page.getByLabel("Source name").fill("Historical source"); await page.getByLabel("Background text").fill("Used a historical technology, not a desired role.");
  await page.getByRole("button", { name: "Add source", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Source added");
  await step(page, /Clarify/); await expect(page.locator(".question-card")).toHaveCount(0);
  await step(page, /Summary/); await expect(page.getByRole("article", { name: "Saved role summary", exact: true })).toHaveCount(0);
  expect((await current(page)).assessment).toBeNull();
});
