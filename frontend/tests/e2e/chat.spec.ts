import { expect, test } from "@playwright/test";
import { MOCK_FAILURE_KEY, MOCK_STORAGE_KEY } from "../../src/lib/mock-transport";

test("chat reviews changes through the shared editor and resumes in both languages", async ({ page }, info) => {
  await page.goto("/");
  await page.getByRole("textbox", { name: "The role you’re looking for", exact: true }).fill("Staff engineer with architecture and hybrid work near Madrid.");
  await page.getByRole("button", { name: "Save draft", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Definition saved");
  await page.getByRole("button", { name: /Chat with assistant|Hablar con el asistente/ }).click();
  const message = page.getByLabel("Your message", { exact: true });
  await message.fill("I can do at most 1 day per week in the office.");
  await page.evaluate(key => sessionStorage.setItem(key, "ai"), MOCK_FAILURE_KEY);
  await page.getByRole("button", { name: "Send message", exact: true }).click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText("unavailable");
  await expect(message).toHaveValue("I can do at most 1 day per week in the office.");
  await page.locator(".locale-switcher select").selectOption("es");
  await expect(page.getByLabel("Tu mensaje", { exact: true })).toHaveValue("I can do at most 1 day per week in the office.");
  await page.getByRole("button", { name: "Enviar mensaje", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Respuesta del chat guardada");
  await expect(page.getByLabel("Conversación guardada")).toContainText("Revisa el cambio propuesto");
  await page.getByRole("button", { name: "Revisar sugerencias del chat", exact: true }).click();
  await page.getByRole("button", { name: "Aplicar las sugerencias revisadas y guardar", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Definición guardada");
  await page.reload();
  await page.getByRole("button", { name: /Chat with assistant|Hablar con el asistente/ }).click();
  await expect(page.getByLabel("Conversación guardada")).toContainText("I can do at most 1 day per week");
  await expect(page.getByRole("button", { name: "Revisar sugerencias del chat", exact: true })).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await expect(page.getByRole("button", { name: "Enviar mensaje", exact: true })).toBeInViewport();
  await page.screenshot({ path: info.outputPath("chat.png"), fullPage: true });
});

test("assistant stays available across every step and preserves its draft when minimized", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("textbox", { name: "The role you’re looking for", exact: true }).fill("Staff architecture, remote in Spain.");
  await page.getByRole("button", { name: "Save draft", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Definition saved");
  const navigation = page.getByRole("navigation", { name: "Definition steps" });
  await expect(navigation.getByRole("button")).toHaveCount(5);
  await expect(navigation.getByRole("button", { name: /Chat/ })).toHaveCount(0);
  const launcher = page.getByRole("button", { name: "Chat with assistant", exact: true });

  for (const step of ["Describe", "Background", "Clarify", "Review & save", "Summary"]) {
    await navigation.getByRole("button", { name: new RegExp(step) }).click();
    await expect(launcher).toBeVisible();
    await launcher.click();
    await expect(page.getByRole("complementary", { name: "Career assistant chat" })).toBeVisible();
    await page.getByLabel("Your message", { exact: true }).fill(`Unsent question from ${step}`);
    await page.getByRole("button", { name: "Minimize assistant", exact: true }).click();
    await expect(launcher).toBeFocused();
    await launcher.click();
    await expect(page.getByLabel("Your message", { exact: true })).toHaveValue(`Unsent question from ${step}`);
    await page.getByLabel("Your message", { exact: true }).press("Escape");
    await expect(launcher).toBeFocused();
  }
  expect(await page.evaluate(key => JSON.parse(localStorage.getItem(key)!).chat ?? [], MOCK_STORAGE_KEY)).toHaveLength(0);
  await launcher.click();
  await page.getByRole("button", { name: "Send message", exact: true }).click();
  await expect(page.getByLabel("Saved conversation")).toContainText("Unsent question from Summary");
  await expect(page.getByRole("status")).toContainText("Chat reply saved");
  expect(await page.evaluate(key => JSON.parse(localStorage.getItem(key)!).chat, MOCK_STORAGE_KEY)).toHaveLength(1);
});

test("first chat starts a draft and failed inference preserves both chat and editor input", async ({ page }) => {
  await page.goto("/");
  const description = page.getByRole("textbox", { name: "The role you’re looking for", exact: true });
  await description.fill("My unfinished description stays here.");
  await page.getByRole("button", { name: "Chat with assistant", exact: true }).click();
  await page.getByLabel("Your message", { exact: true }).fill("I want a Staff role with architecture.");
  await page.evaluate(key => sessionStorage.setItem(key, "ai"), MOCK_FAILURE_KEY);
  await page.getByRole("button", { name: "Send message", exact: true }).click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText("unavailable");
  await expect(page.getByLabel("Your message", { exact: true })).toHaveValue("I want a Staff role with architecture.");
  await expect(description).toHaveValue("My unfinished description stays here.");
  await page.getByRole("button", { name: "Send message", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Chat reply saved");
  await expect(page.getByLabel("Saved conversation")).toContainText("I want a Staff role with architecture.");
  await expect(description).toHaveValue("My unfinished description stays here.");
});

test("chat can discuss changes while structured suggestions and manual edits remain pending", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("textbox", { name: "The role you’re looking for", exact: true }).fill("Staff architecture with hybrid work near Madrid.");
  await page.getByRole("button", { name: "Save draft", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Definition saved");
  await page.locator(".sidebar nav").getByRole("button", { name: /Clarify/ }).click();
  await page.getByRole("button", { name: "Request clarification & suggestions", exact: true }).click();
  await expect(page.getByText("Suggestions awaiting review", { exact: true })).toBeVisible();
  await page.locator(".sidebar nav").getByRole("button", { name: /Review & save/ }).click();
  const seniority = page.locator(".criterion").filter({ has: page.locator('input[value="seniority"]') });
  await seniority.getByRole("textbox", { name: "Value", exact: true }).fill("Principal — still deciding");
  await page.getByRole("button", { name: "Chat with assistant", exact: true }).click();
  await page.getByLabel("Your message", { exact: true }).fill("Change my office limit to at most 1 day per week.");
  await page.getByRole("button", { name: "Send message", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Chat reply saved");
  await expect(page.getByRole("button", { name: "Review chat suggestions", exact: true })).toBeDisabled();
  await expect(seniority.getByRole("textbox", { name: "Value", exact: true })).toHaveValue("Principal — still deciding");
  await page.getByRole("button", { name: "Minimize assistant", exact: true }).click();
  await expect(page.getByText("The suggestion context has changed", { exact: true })).toBeVisible();
});
