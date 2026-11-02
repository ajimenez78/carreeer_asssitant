import React from "react";
import { mkdirSync, writeFileSync } from "node:fs";
import { renderToStaticMarkup } from "react-dom/server";
import { expect, test } from "@playwright/test";
import { PreferenceEditor } from "../../src/components/preference-editor";
import { SourceReview } from "../../src/components/background";
import { QuestionCard } from "../../src/components/question-card";
import { ApiError, createClient, type Transport } from "../../src/lib/client";
import { createMockTransport, MOCK_AI_DELAY_KEY, MOCK_FAILURE_KEY, MOCK_STORAGE_KEY } from "../../src/lib/mock-transport";
import { emptyCompensation, validateDefinition } from "../../src/lib/preferences";
import type { Preference, SaveDefinition } from "../../src/lib/contracts";

function memory() {
  const values = new Map<string, string>();
  return { getItem: (k: string) => values.get(k) ?? null, setItem: (k: string, v: string) => { values.set(k, v); }, removeItem: (k: string) => { values.delete(k); } };
}
function setup() { const storage = memory(), failures = memory(); return { storage, failures, api: createClient(createMockTransport(storage, failures, 0)) }; }
const draft: SaveDefinition = { description: "Staff architecture role. Remote preferred; hybrid near Madrid at most two days, no frontend-only work.", state: "draft", preferences: [] };
const salary: Preference = { key: "salary", category: "compensation", priority: "preferred", value: null, note: null };
const noop = () => {};

test("criterion component renders explicit unknowns and accessible labels without guessing salary", () => {
  const html = renderToStaticMarkup(<PreferenceEditor preference={salary} index={0} onChange={noop} onRemove={noop} />);
  expect(html).toContain('for="criterion-0-name"');
  expect(html).toContain('value="unknown" selected=""');
  expect(html).toContain("Unknown — leave this open");
  expect(html).not.toContain("EUR");
  expect(html).toContain("Mandatory"); expect(html).toContain("Preferred"); expect(html).toContain("Excluded");
});

test("structured components preserve an unknown office-day period and nullable pay details", () => {
  const onsite = { ...salary, category: "work_arrangement" as const, value: { days: 2, period: null } };
  const html = renderToStaticMarkup(<PreferenceEditor preference={onsite} index={0} onChange={noop} onRemove={noop} />);
  expect(html).toContain('value="2"'); expect(html).toContain('value="" selected=""');
  const pay = renderToStaticMarkup(<PreferenceEditor preference={{ ...salary, value: emptyCompensation }} index={1} onChange={noop} onRemove={noop} />);
  expect(pay).toContain("Blank fields remain unknown"); expect(pay).toContain("Tax basis");
});

test("background and question components keep provenance, escaped text, and answer states", async () => {
  const { api } = setup(); await api.save(draft);
  const source = await api.addSource({ kind: "text", display_name: "CV", text: "<script>example</script>\nPreviously used SQL." });
  const run = async () => true;
  const html = renderToStaticMarkup(<SourceReview source={source} api={api} run={run} language="English" onSaved={async () => {}} />);
  expect(html).toContain("Provenance: CV"); expect(html).toContain("&lt;script&gt;"); expect(html).not.toContain("<script>");
  const result = await api.clarify("English");
  const question = await api.answer(result.clarifications[0].id, "unknown");
  const q = renderToStaticMarkup(<QuestionCard question={question} api={api} run={run} onSaved={noop} />);
  expect(q).toContain("Explicitly unknown"); expect(q).toContain("Skip question");
});

test("mocked workflow uses Part 7 request and response envelopes", async () => {
  const storage = memory();
  const transport = createMockTransport(storage, undefined, 0);
  const samples: { schema: string; value: unknown }[] = [];
  const routes: { path: string; method: string; multipart: boolean }[] = [];
  const recording: Transport = async (path, init) => { routes.push({ path, method: init.method!, multipart: init.body instanceof FormData }); return transport(path, init); };
  const api = createClient(recording);
  samples.push({ schema: "SaveDefinition", value: draft });
  samples.push({ schema: "DefinitionView", value: await api.save(draft) });
  const input = { kind: "text" as const, display_name: "CV", text: "Built distributed systems.\nUsed SQL in a previous role." };
  samples.push({ schema: "SourceInput", value: input });
  const source = await api.addSource(input);
  samples.push({ schema: "SourceView", value: source });
  samples.push({ schema: "BackgroundView", value: await api.suggestFacts(source.id, "English") });
  await api.reviewSource(source.id, ["Built distributed systems."]);
  samples.push({ schema: "ClarificationControl", value: { paused: false } });
  samples.push({ schema: "DefinitionView", value: await api.controlClarification(false) });
  const proposal = await api.clarify("English");
  samples.push({ schema: "ClarificationView", value: proposal });
  const saved = await api.save({ ...draft, preferences: proposal.proposal.preferences, proposal_context: proposal.proposal_context });
  samples.push({ schema: "DefinitionView", value: saved });
  expect(saved.preferences.find(p => p.key === "salary")?.value).toBeNull();
  expect(saved.preferences.find(p => p.key === "onsite_limit")?.value).toEqual({ days: 2, period: null });
  expect(saved.preferences.some(p => JSON.stringify(p).includes("SQL"))).toBe(false);
  for (const [i, state] of ["answered", "skipped", "unknown"].entries()) {
    const answer = { state, ...(state === "answered" ? { answer: "Still considering compensation" } : {}) };
    samples.push({ schema: "Answer", value: answer });
    samples.push({ schema: "QuestionView", value: await api.answer(proposal.clarifications[i].id, state as "answered" | "skipped" | "unknown", state === "answered" ? "Still considering compensation" : undefined) });
  }
  const file = new File(["# CV\nArchitecture"], "cv.md", { type: "text/markdown" });
  await api.addSource(file);
  expect(routes).toContainEqual({ path: "/job-definition/sources", method: "POST", multipart: true });
  const reopened = await createClient(createMockTransport(storage, undefined, 0)).read();
  expect(reopened.preferences).toEqual(saved.preferences);
  const chatInput = { request_id: crypto.randomUUID(), message: "At most 1 day per week in the office", language: "Spanish" as const };
  samples.push({ schema: "ChatInput", value: chatInput });
  const turn = await api.sendChat(chatInput.message, chatInput.language, chatInput.request_id);
  samples.push({ schema: "ChatTurnView", value: turn });
  samples.push({ schema: "ChatView", value: await api.chat() });
  expect((await api.read()).preferences).toEqual(saved.preferences);
  expect((await api.chat()).turns).toHaveLength(1);
  samples.push({ schema: "CleanupView", value: await api.removeSource(source.id) });
  expect((await api.chat()).turns).toEqual([]);
  expect((await api.read()).clarifications).toEqual([]);
  expect((await api.read()).preferences).toEqual(saved.preferences);
  samples.push({ schema: "CleanupView", value: await api.remove() });
  mkdirSync("test-results", { recursive: true });
  writeFileSync("test-results/mock-contract.json", JSON.stringify(samples));
});

test("failed saves and AI calls preserve the previously saved draft", async () => {
  const { api, failures } = setup(); const accepted = await api.save(draft);
  failures.setItem(MOCK_FAILURE_KEY, "save");
  await expect(api.save({ ...draft, description: "Changed description" })).rejects.toMatchObject({ status: 503 });
  failures.setItem(MOCK_FAILURE_KEY, "ai");
  await expect(api.clarify("English")).rejects.toMatchObject({ status: 503 });
  expect(await api.read()).toEqual(accepted);
});

test("an answer or source review invalidates a pending proposal without applying it", async () => {
  const { api } = setup(); await api.save(draft);
  const proposal = await api.clarify("English");
  await api.answer(proposal.clarifications[0].id, "skipped");
  await expect(api.save({ ...draft, preferences: proposal.proposal.preferences, proposal_context: proposal.proposal_context })).rejects.toMatchObject({ status: 409 });
  expect((await api.read()).preferences).toEqual([]);
  const source = await api.addSource({ kind: "text", display_name: "CV", text: "Historical experience" });
  await api.reviewSource(source.id, []);
  expect((await api.read()).clarifications).toEqual([]);
});

test("uploads enforce format, size, count and recovery contracts", async () => {
  const { api } = setup(); await api.save(draft);
  await expect(api.addSource(new File(["x"], "cv.exe"))).rejects.toMatchObject({ status: 415 });
  await expect(api.addSource(new File([], "cv.pdf"))).rejects.toMatchObject({ status: 413 });
  await expect(api.addSource(new File([new Uint8Array(10 * 1024 * 1024 + 1)], "cv.pdf"))).rejects.toMatchObject({ status: 413 });
  for (const extension of ["pdf", "doc", "docx", "md", "markdown"]) await api.addSource(new File(["CV"], `cv.${extension}`));
  await expect(api.addSource(new File(["CV"], "sixth.md"))).rejects.toMatchObject({ status: 409 });
  const failed = await api.addSource({ kind: "url", display_name: "Profile", url: "https://www.linkedin.com/in/example" });
  expect(failed.extraction_state).toBe("failed"); expect(failed.extraction_error?.message).toContain("paste");
  expect((await api.retrySource(failed.id)).extraction_state).toBe("failed");
  await api.removeSource(failed.id); expect((await api.read()).sources).toHaveLength(5);
});

test("frontend validation handles real domain boundaries", () => {
  expect(validateDefinition({ ...draft, description: " " })).toContain("description");
  expect(validateDefinition({ ...draft, preferences: [salary, salary] })).toContain("unique");
  expect(validateDefinition({ ...draft, preferences: [{ ...salary, value: { ...emptyCompensation, minimum: 10, maximum: 5 } }] })).toContain("Minimum");
  expect(validateDefinition({ ...draft, preferences: [{ ...salary, value: { ...emptyCompensation, currency: "EU" } }] })).toContain("currency");
  expect(validateDefinition({ ...draft, preferences: [{ ...salary, category: "work_arrangement", value: { days: 1.5, period: null } }] })).toContain("whole number");
  expect(validateDefinition({ ...draft, preferences: [salary] })).toBeNull();
  expect(validateDefinition({ ...draft, preferences: [{ ...salary, category: "role", value: ",".repeat(2500) }] })).toBeNull();
  expect(validateDefinition({ ...draft, preferences: [{ ...salary, category: "role", value: "x".repeat(3999) }] })).toContain("4,000");
});

test("storage errors return an actionable failure without claiming a save", async () => {
  const storage = memory(); await createClient(createMockTransport(storage, undefined, 0)).save(draft);
  const before = storage.getItem(MOCK_STORAGE_KEY);
  const api = createClient(createMockTransport({ ...storage, setItem: () => { throw new Error("QuotaExceeded"); } }, undefined, 0));
  await expect(api.save({ ...draft, description: "An edit" })).rejects.toMatchObject({ code: "mock_storage" });
  expect(storage.getItem(MOCK_STORAGE_KEY)).toBe(before);
});

test("request boundary converts connection failures into recoverable errors", async () => {
  const api = createClient(async () => { throw new Error("internal transport details"); });
  await expect(api.read()).rejects.toBeInstanceOf(ApiError);
  await expect(api.read()).rejects.toThrow("Your input is still here");
});

test("readiness is system-owned, summary uses saved content, and control preserves work", async () => {
  const { api } = setup();
  const clear = { description: "Staff architect designing distributed systems, remote in Spain. Salary is flexible.", state: "ready" as const, preferences: [] };
  expect((await api.save(clear)).state).toBe("draft");
  const result = await api.clarify("English");
  expect(result.assessment.sufficient).toBe(true);
  expect(result.assessment.summary).toContain(clear.description);
  expect((await api.read()).preferences).toEqual([]);
  expect((await api.save({ ...clear, state: "draft" })).assessment).toEqual(result.assessment);
  expect((await api.controlClarification(true)).state).toBe("ready");
  await expect(api.clarify("English")).rejects.toMatchObject({ status: 409 });
  await api.controlClarification(false);
  await expect(api.save({ ...clear, preferences: result.proposal.preferences, proposal_context: result.proposal_context })).rejects.toMatchObject({ status: 409 });
  const edited = await api.save({ ...clear, description: "An unclear new direction" });
  expect(edited.state).toBe("draft"); expect(edited.assessment).toBeNull();
});

test("canceling a mock assessment never persists late questions or a summary", async () => {
  const { storage, failures } = setup();
  const api = createClient(createMockTransport(storage, failures, 0));
  await api.save(draft); failures.setItem(MOCK_AI_DELAY_KEY, "1000");
  const controller = new AbortController();
  const pending = api.clarify("English", controller.signal);
  controller.abort();
  await expect(pending).rejects.toMatchObject({ name: "AbortError" });
  await api.controlClarification(true);
  const current = await api.read();
  expect(current.clarification_paused).toBe(true);
  expect(current.assessment).toBeNull(); expect(current.clarifications).toEqual([]);
});

test("stop then resume rejects an uncanceled assessment from the previous context", async () => {
  const { api, failures } = setup();
  await api.save(draft);
  failures.setItem(MOCK_AI_DELAY_KEY, "500");
  const pending = api.clarify("English");
  const rejected = expect(pending).rejects.toMatchObject({ status: 409, code: "stale_proposal" });
  await api.controlClarification(true);
  await api.controlClarification(false);
  await rejected;
  const current = await api.read();
  expect(current.clarification_paused).toBe(false);
  expect(current.assessment).toBeNull(); expect(current.clarifications).toEqual([]);
  expect(current.preferences).toEqual([]);
});

test("source mutations remove derived summary prose and preserve saved preferences", async () => {
  const { api } = setup(); await api.save(draft);
  const first = await api.clarify("English"); expect(first.assessment.summary).not.toBe("");
  const source = await api.addSource({ kind: "text", display_name: "CV", text: "Historical experience" });
  expect((await api.read()).assessment).toBeNull();
  expect((await api.read()).clarifications).toEqual([]);
  await api.clarify("English"); await api.reviewSource(source.id, []);
  expect((await api.read()).assessment).toBeNull();
  await api.clarify("English"); await api.removeSource(source.id);
  const current = await api.read();
  expect(current.assessment).toBeNull(); expect(current.preferences).toEqual([]);
});


test("chat proposals require the same explicit save and cannot erase omitted criteria", async () => {
  const { api } = setup();
  await api.save({ ...draft, preferences: [{ key: "seniority", category: "seniority", priority: "mandatory", value: "Staff", note: null }] });
  const id = crypto.randomUUID();
  const turn = await api.sendChat("At most 1 day per week", "English", id);
  expect(turn.has_changes).toBe(true);
  expect((await api.read()).preferences).toHaveLength(1);
  expect(await api.sendChat("At most 1 day per week", "English", id)).toEqual(turn);
  expect((await api.chat()).turns).toHaveLength(1);
  await api.save({ ...draft, preferences: turn.proposal.preferences, proposal_context: turn.proposal_context });
  expect((await api.read()).preferences.find(p => p.key === "seniority")?.value).toBe("Staff");
  expect((await api.read()).preferences.find(p => p.key === "onsite_limit")?.value).toEqual({ days: 1, period: "week" });
  await expect(api.save({ ...draft, preferences: turn.proposal.preferences, proposal_context: turn.proposal_context })).rejects.toMatchObject({ status: 409 });
});
