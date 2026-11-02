import type { BackgroundProposal, ClarificationProposal, Definition, Preference, SaveDefinition, SourceInput, SourceMetadata, SourceView } from "./contracts";
import type { Transport } from "./client";
import { validateDefinition } from "./preferences";

export const MOCK_STORAGE_KEY = "career-assistant:mock:v1";
export const MOCK_FAILURE_KEY = "career-assistant:mock-failure";
type Snapshot = { definition: Definition | null; sources: SourceView[] };
type Storage = Pick<globalThis.Storage, "getItem" | "setItem" | "removeItem">;
const usage = { model: "mock", input_tokens: 0, output_tokens: 0, estimated_cost_usd: "0" };
const cleanup = { cleanup_pending: false, pending_originals: 0 };
const json = (data: unknown, status = 200) => Response.json(data, { status });
const fail = (status: number, code: string, message: string) => json({ error: { code, message, fields: {} } }, status);
const metadata = (s: SourceView): SourceMetadata => ({ id: s.id, kind: s.kind, display_name: s.display_name, url: s.url, media_type: s.media_type, size_bytes: s.size_bytes, extraction_state: s.extraction_state, extraction_error: s.extraction_error, original_stored: s.original_stored, reviewed_at: s.reviewed_at, created_at: s.created_at });
async function fingerprint(snapshot: Snapshot) {
  const bytes = new TextEncoder().encode(JSON.stringify(snapshot));
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, "0")).join("");
}

// Local-only request adapter. No fetch, parser, provider, authentication, or original
// storage is used. Binary-document extraction and job suggestions are fixtures.
export function createMockTransport(storage: Storage, failures?: Storage, delay = 180): Transport {
  return async (path, init) => {
    await new Promise(resolve => setTimeout(resolve, delay));
    const method = init.method ?? "GET";
    const route = path.replace(/^\/job-definition/, "");
    const operation = route.endsWith("/facts") || route === "/clarifications" ? "ai"
      : route === "/sources" ? "upload" : route.includes("clarifications/") ? "answer"
      : route.includes("sources/") && method === "PATCH" ? "source-review"
      : method === "PUT" ? "save" : "read";
    if (failures?.getItem(MOCK_FAILURE_KEY) === operation) {
      failures.removeItem(MOCK_FAILURE_KEY);
      return fail(503, `${operation}_unavailable`, operation === "ai" ? "The assistant is unavailable. Your saved draft and typed input are safe. Try again." : "This request could not be completed. Your input is still here. Try again.");
    }
    try {
      const snapshot: Snapshot = JSON.parse(storage.getItem(MOCK_STORAGE_KEY) ?? '{"definition":null,"sources":[]}');
      const d = snapshot.definition;
      const body = typeof init.body === "string" ? JSON.parse(init.body) : undefined;
      const persist = () => {
        if (snapshot.definition) snapshot.definition.sources = snapshot.sources.map(metadata);
        storage.setItem(MOCK_STORAGE_KEY, JSON.stringify(snapshot));
      };
      if (route === "/cleanup" && method === "POST") return json(cleanup);
      if (!route && method === "PUT") {
        const data = body as SaveDefinition;
        const error = validateDefinition(data);
        if (error) return fail(422, "validation", error);
        if (data.proposal_context && data.proposal_context !== await fingerprint(snapshot)) return fail(409, "stale_proposal", "The context changed. Discard the suggestions and request a fresh review, or keep your edits as manual criteria.");
        const now = new Date().toISOString();
        snapshot.definition = { id: d?.id ?? crypto.randomUUID(), created_at: d?.created_at ?? now, updated_at: now, description: data.description.trim(), state: data.state, preferences: data.preferences.map(p => ({ ...p, key: p.key.trim() })), sources: [], clarifications: d?.clarifications ?? [] };
        persist(); return json(snapshot.definition);
      }
      if (!d) return fail(404, "not_found", "Save an initial description to start your definition.");
      if (!route && method === "GET") return json(d);
      if (!route && method === "DELETE") { snapshot.definition = null; snapshot.sources = []; persist(); return json(cleanup); }
      if (route === "/sources" && method === "POST") {
        let input: SourceInput | undefined;
        const file = init.body instanceof FormData ? init.body.get("file") as File : null;
        if (file) {
          if (!/\.(pdf|docx?|md|markdown)$/i.test(file.name)) return fail(415, "unsupported_format", "Choose a PDF, DOC, DOCX, or Markdown file.");
          if (!file.size || file.size > 10 * 1024 * 1024) return fail(413, "file_size", "Choose a nonempty file no larger than 10 MB.");
          if (snapshot.sources.filter(s => s.kind === "file").length >= 5) return fail(409, "file_limit", "You can retain five files. Remove one before uploading another.");
        } else input = body as SourceInput;
        if (input && (!input.display_name.trim() || input.display_name.length > 200)) return fail(422, "validation", "Enter a source name of 1–200 characters.");
        if (input?.kind === "text" && (!input.text.trim() || input.text.length > 60000)) return fail(422, "validation", "Paste 1–60,000 characters of background text.");
        if (input?.kind === "url") {
          let url: URL;
          try { url = new URL(input.url); } catch { return fail(422, "validation", "Enter a public HTTP or HTTPS URL."); }
          if (!["http:", "https:"].includes(url.protocol) || url.username || url.password || url.port || input.url.length > 2048) return fail(422, "validation", "Use a public HTTP or HTTPS URL with a standard port and no credentials.");
        }
        const blocked = input?.kind === "url" && /linkedin|restricted|localhost|127\.0\.0\.1/.test(input.url);
        const scanned = file && /scanned/i.test(file.name);
        const text = input?.kind === "text" ? input.text : file && /\.(md|markdown)$/i.test(file.name) ? await file.text() : "Worked on distributed systems.\nCollaborated with engineering teams.";
        if (text.length > 60000) return fail(422, "text_limit", "The extracted text exceeds 60,000 characters. Use a shorter source.");
        const source: SourceView = {
          id: crypto.randomUUID(), kind: file ? "file" : input!.kind, display_name: file?.name ?? input!.display_name.trim(),
          url: input?.kind === "url" ? input.url : null, media_type: file?.type || null, size_bytes: file?.size ?? null,
          extraction_state: blocked || scanned ? "failed" : "ready", original_stored: Boolean(file),
          extraction_error: blocked || scanned ? { code: "extraction_failed", message: blocked ? "This page could not be retrieved. Upload a document or paste its text instead." : "No readable text was found. Upload a text-based document or paste the text; scanned-document OCR is not available." } : null,
          reviewed_at: null, created_at: new Date().toISOString(), extracted_text: blocked || scanned ? null : text, facts: [],
        };
        snapshot.sources.push(source); persist(); return json(source, 201);
      }
      if (route.startsWith("/sources/")) {
        const [, , id, action] = route.split("/");
        const source = snapshot.sources.find(s => s.id === id);
        if (!source) return fail(404, "not_found", "This source no longer exists.");
        if (method === "GET" && !action) return json(source);
        if (method === "DELETE" && !action) {
          snapshot.sources = snapshot.sources.filter(s => s.id !== id); d.clarifications = []; persist(); return json(cleanup);
        }
        if (method === "POST" && action === "retry") {
          source.reviewed_at = null; source.facts = []; d.clarifications = [];
          if (source.extraction_state === "pending") { source.extraction_state = "ready"; source.extracted_text = "Worked on distributed systems."; }
          persist(); return json(source);
        }
        if (source.extraction_state !== "ready") return fail(409, "source_not_ready", "Retry extraction, upload another file, or paste the source text first.");
        if (method === "PATCH" && !action) {
          const facts = body.facts as string[];
          if (facts.length > 100 || facts.some(f => !f.trim() || f.length > 2000)) return fail(422, "validation", "Use at most 100 facts, each 1–2,000 characters.");
          source.facts = facts.map(content => ({ id: crypto.randomUUID(), source_id: id, content: content.trim() }));
          source.reviewed_at = new Date().toISOString(); d.clarifications = []; persist(); return json(source);
        }
        if (method === "POST" && action === "facts") {
          const facts = (source.extracted_text ?? "").split(/\n/).map(s => s.trim()).filter(Boolean).slice(0, 20).map(s => ({ content: s.slice(0, 2000), evidence: s.slice(0, 2000) }));
          return json({ source_id: id, proposal: { facts, unknowns: [] }, usage } satisfies BackgroundProposal);
        }
      }
      if (route === "/clarifications" && method === "POST") {
        const round = crypto.randomUUID();
        const questions = body.language === "Spanish"
          ? ["¿Qué rango salarial, moneda, periodo y base bruta o neta prefieres?", "Si aceptas trabajo híbrido, ¿los días de oficina se cuentan por semana, mes o año?", "¿Qué horario o límites de conciliación son importantes para ti?"]
          : ["What salary range, currency, pay period, and gross or net basis would you prefer?", "If hybrid work is acceptable, are office days counted per week, month, or year?", "What working hours or work–life balance boundaries matter to you?"];
        const added = questions.filter(q => !d.clarifications.some(old => old.question === q)).map((question, position) => ({ id: crypto.randomUUID(), round_id: round, position, question, answer_state: "unanswered" as const, answer: null }));
        const suggested: Preference[] = [];
        const add = (key: string, category: Preference["category"], value: Preference["value"], priority: Preference["priority"] = "preferred", note: string | null = null) => { if (!d.preferences.some(p => p.key === key)) suggested.push({ key, category, value, priority, note }); };
        if (/staff/i.test(d.description)) add("seniority", "seniority", "Staff", "mandatory");
        if (/architect|arquitect/i.test(d.description)) add("architecture", "responsibilities", "Architecture and system design");
        if (/cross.team|entre equipos/i.test(d.description)) add("cross_team", "responsibilities", "Collaboration across teams");
        if (/learning|aprendizaje/i.test(d.description)) add("learning", "company_context", "Continuous learning");
        if (/international|internacional/i.test(d.description)) add("international", "company_context", "International scope");
        if (/ai engineering|ingenier[ií]a de ia/i.test(d.description)) add("ai_engineering", "technical_interests", "AI engineering");
        if (/remote|remoto/i.test(d.description)) add("remote", "work_arrangement", true);
        if (/madrid/i.test(d.description)) add("hybrid_location", "location", "Madrid or nearby", "mandatory", "If hybrid");
        if (/two|2|dos/i.test(d.description)) add("onsite_limit", "work_arrangement", { days: 2, period: null }, "mandatory", "If hybrid; clarify the period");
        if (/frontend/i.test(d.description)) add("frontend_only", "responsibilities", "Frontend-only work", "excluded");
        add("salary", "compensation", null);
        d.clarifications.push(...added); persist();
        return json({ proposal: { preferences: [...d.preferences, ...suggested], conflicts: [] }, clarifications: added, proposal_context: await fingerprint(snapshot), usage } satisfies ClarificationProposal);
      }
      if (route.startsWith("/clarifications/") && method === "PATCH") {
        const q = d.clarifications.find(q => q.id === route.split("/")[2]);
        if (!q) return fail(404, "not_found", "This question is no longer current. Request a fresh clarification round.");
        if (!["answered", "skipped", "unknown"].includes(body.state) || (body.state === "answered" && (!body.answer?.trim() || body.answer.length > 4000))) return fail(422, "validation", "Enter an answer of 1–4,000 characters, skip, or mark it unknown.");
        q.answer_state = body.state; q.answer = body.state === "answered" ? body.answer.trim() : null; persist(); return json(q);
      }
      return fail(404, "not_found", "This mock request is not supported.");
    } catch {
      return fail(503, "mock_storage", "Browser storage is unavailable or full. Your typed input is still here. Enable storage or free space, then try again.");
    }
  };
}
