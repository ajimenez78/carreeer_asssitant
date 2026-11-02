import { useI18n } from "../lib/i18n/provider";
import { useRef, useState } from "react";
import type { Client } from "../lib/client";
import { ApiError } from "../lib/client";
import type { BackgroundProposal, Cleanup, Definition, Language, SourceView } from "../lib/contracts";

export type Run = (task: () => Promise<void>, message?: string) => Promise<boolean>;
export function Background({ api, definition, run, language, onAdded, onReviewed, onRemoved, onCleanup }: { api: Client; definition: Definition; run: Run; language: Language; onAdded: (s: SourceView) => void; onReviewed: (s: SourceView) => void; onRemoved: (id: string) => void; onCleanup: (result: Cleanup) => void }) {
  const { t } = useI18n();
  const [kind, setKind] = useState<"file" | "url" | "text">("file");
  const [name, setName] = useState("");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [selected, setSelected] = useState<SourceView | null>(null);
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  async function add() {
    const ok = await run(async () => {
      if (kind === "file" && !file) throw new Error("Choose a document first.");
      try {
        const source = await api.addSource(kind === "file" ? file! : kind === "text" ? { kind, display_name: name, text } : { kind, display_name: name, url });
        setSelected(source); onAdded(source);
      } catch (error) {
        if (error instanceof ApiError && typeof error.fields.source_id === "string") {
          const reserved = await api.source(error.fields.source_id);
          setSelected(reserved); onAdded(reserved);
        }
        throw error;
      }
    }, "Source added. Review its background before accepting any facts.");
    if (ok) { setName(""); setText(""); setUrl(""); setFile(null); if (fileInput.current) fileInput.current.value = ""; }
  }
  return <>
    <p className="section-kicker">{t("02 / Background")}</p><h2>{t("Your experience, with context.")}</h2><p className="section-intro">{t("Add a CV, profile, or notes. Background facts describe your past; they do not become job requirements automatically.")}</p>
    <form noValidate onSubmit={e => { e.preventDefault(); void add(); }} className="card">
      <h3>{t("Add a source")}</h3>
      <label>{t("Source type")}<select value={kind} onChange={e => { setKind(e.target.value as typeof kind); setFile(null); }}><option value="file">{t("Upload a document")}</option><option value="url">{t("Public link")}</option><option value="text">{t("Paste text")}</option></select></label>
      <div key={kind}>{kind === "file" ? <><label>{t("Document")}<input ref={fileInput} type="file" accept=".pdf,.doc,.docx,.md,.markdown" onChange={e => setFile(e.target.files?.[0] ?? null)} /></label><p className="hint">{t("Text-based PDF, DOC, DOCX, or Markdown. Up to five files, 10 MB each. Scanned-document OCR is deferred.")} {definition.sources.filter(s => s.kind === "file").length}{t("/5 files retained.")}</p></> : <><label>{t("Source name")}<input maxLength={200} required value={name} onChange={e => setName(e.target.value)} placeholder={t("For example: CV or public profile")} /></label>{kind === "url" ? <><label>{t("Public URL")}<input type="url" required maxLength={2048} value={url} onChange={e => setUrl(e.target.value)} placeholder="https://example.com/profile" /></label><p className="hint">{t("Restricted pages may need an uploaded export or pasted text.")}</p></> : <label>{t("Background text")}<textarea required maxLength={60000} rows={6} value={text} onChange={e => setText(e.target.value)} /></label>}</>}</div>
      <button className="primary" type="submit">{t("Add source")}</button>
    </form>
    <div className="source-list"><h3>{t("Saved sources")}</h3>{definition.sources.length === 0 && <p className="empty">{t("No sources yet. Background is optional; you can continue to clarification.")}</p>}{definition.sources.map(s => <article className="source-item" key={s.id}>
      <div><strong>{s.display_name}</strong><p className="hint">{s.kind === "url" ? s.url : s.kind === "file" ? t("Uploaded document") : t("Pasted text")}</p><span className={`badge ${s.extraction_state === "failed" ? "failed" : ""}`}>{s.extraction_state === "ready" ? s.reviewed_at ? t("Background reviewed") : t("Ready for review") : s.extraction_state === "failed" ? t("Extraction failed") : t("Processing pending")}</span></div>
      <div className="actions"><button type="button" onClick={() => void run(async () => setSelected(await api.source(s.id)))}>{t("Review")} {s.display_name}</button><button type="button" className="text-button danger" onClick={() => setConfirmId(s.id)}>{t("Remove")} {s.display_name}</button></div>
      {confirmId === s.id && <div className="confirmation"><p>{t("Removing this source deletes its text and facts and clears all clarification questions and answers. Accepted job criteria remain. Backup copies expire within seven days.")}</p><div className="actions"><button type="button" className="danger" onClick={() => void run(async () => { onCleanup(await api.removeSource(s.id)); if (selected?.id === s.id) setSelected(null); setConfirmId(null); onRemoved(s.id); }, "Source removed. Accepted criteria were preserved.")}>{t("Confirm remove source")}</button><button type="button" onClick={() => setConfirmId(null)}>{t("Cancel")}</button></div></div>}
    </article>)}</div>
    {selected && <SourceReview key={`${selected.id}-${selected.reviewed_at}-${selected.extraction_state}`} source={selected} api={api} run={run} language={language} onSaved={async source => { setSelected(source); onReviewed(source); }} />}
  </>;
}

export function SourceReview({ source, api, run, language, onSaved }: { source: SourceView; api: Client; run: Run; language: Language; onSaved: (s: SourceView) => Promise<void> }) {
  const { t } = useI18n();
  const [facts, setFacts] = useState(source.facts.map(f => f.content).join("\n"));
  const [proposal, setProposal] = useState<BackgroundProposal | null>(null);
  return <section className="card background-review" aria-label={t("Background review: {name}", { name: source.display_name })}>
    <h3>{t("Review background:")} {source.display_name}</h3><p className="hint">{t("Provenance:")} {source.url ?? source.display_name}{t(". Only explicitly accepted facts are used in clarification.")}</p>
    {source.extraction_state !== "ready" ? <><p className="inline-error">{t(source.extraction_error?.message ?? "Processing has not finished. Retry extraction or remove this source.")}</p>{source.kind !== "file" || source.original_stored ? <button type="button" onClick={() => void run(async () => onSaved(await api.retrySource(source.id)), "Extraction retried. Review the source status.")}>{t("Retry extraction")}</button> : <p>{t("There is no stored original. Remove this source and upload it again.")}</p>}<p className="hint">{t("You can also use “Paste text” or upload a text-based replacement above.")}</p></> : <>
      <details><summary>{t("Read extracted text")}</summary><pre className="source-text">{source.extracted_text}</pre></details>
      <p>{t("Check each fact against the source. Correct mistakes or omit facts that should not be used.")}</p>
      <button type="button" onClick={() => void run(async () => { const result = await api.suggestFacts(source.id, language); setProposal(result); setFacts(result.proposal.facts.map(f => f.content).join("\n")); }, "Suggested facts are ready for your review; they have not been accepted.")}>{t("Suggest background facts")}</button>
      {proposal && <div className="evidence"><h4>{t("Source evidence")}</h4>{proposal.proposal.facts.map((f, i) => <blockquote key={i}>{f.evidence}</blockquote>)}{proposal.proposal.unknowns.map(u => <p key={u}>{t("Unknown:")} {u}</p>)}</div>}
      <label>{t("Reviewed facts, one per line")}<textarea rows={6} value={facts} onChange={e => setFacts(e.target.value)} placeholder={t("Enter or correct historical facts. Leave blank to accept no facts.")} /></label>
      <p className="hint">{t("Up to 100 facts, 2,000 characters each. Accepting facts saves this source review immediately and clears derived questions and answers.")}</p>
      <button type="button" className="primary" onClick={() => void run(async () => { const lines = facts.split("\n").map(f => f.trim()).filter(Boolean); await onSaved(await api.reviewSource(source.id, lines)); }, "Background facts accepted. Job preferences have not changed.")}>{t("Accept reviewed facts")}</button>
    </>}
  </section>;
}
