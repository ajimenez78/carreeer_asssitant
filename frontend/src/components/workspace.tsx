"use client";

import { useI18n } from "../lib/i18n/provider";
import { locales } from "../lib/i18n/catalogs";

import { useEffect, useState } from "react";
import { ApiError, createClient } from "../lib/client";
import type { ClarificationProposal, Definition, Language, Preference } from "../lib/contracts";
import { createMockTransport } from "../lib/mock-transport";
import { newPreference, validateDefinition } from "../lib/preferences";
import { Background, type Run } from "./background";
import { PreferenceEditor } from "./preference-editor";
import { QuestionCard } from "./question-card";

const api = createClient((path, init) => createMockTransport(window.localStorage, window.sessionStorage)(path, init));
const steps = ["Describe", "Background", "Clarify", "Review & save"];

export function Workspace() {
  const { t, locale } = useI18n();
  const [definition, setDefinition] = useState<Definition | null>(null);
  const [description, setDescription] = useState("");
  const [state, setState] = useState<"draft" | "ready">("draft");
  const [preferences, setPreferences] = useState<Preference[]>([]);
  const [step, setStep] = useState(0);
  const [assistanceOverride, setAssistanceOverride] = useState<Language | null>(null);
  const language: Language = assistanceOverride ?? locales[locale].assistanceLanguage;
  const [proposal, setProposal] = useState<ClarificationProposal | null>(null);
  const [stale, setStale] = useState(false);
  const [busy, setBusy] = useState(true);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("Opening your workspace…");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const dirty = description !== (definition?.description ?? "") || state !== (definition?.state ?? "draft") || JSON.stringify(preferences) !== JSON.stringify(definition?.preferences ?? []);
  const unsaved = dirty || proposal !== null;

  function open(d: Definition | null) {
    setDefinition(d); setDescription(d?.description ?? ""); setState(d?.state ?? "draft"); setPreferences(d?.preferences ?? []); setProposal(null); setStale(false);
  }
  async function load() {
    try { const d = await api.read(); open(d); setMessage("Saved definition reopened. Continue wherever you left off."); }
    catch (e) { if (e instanceof ApiError && e.status === 404) { open(null); setMessage("Start with a rough idea. You can save an incomplete draft."); } else throw e; }
    setLoaded(true);
  }
  useEffect(() => {
    let active = true;
    api.read().then(d => { if (active) { open(d); setLoaded(true); setMessage("Saved definition reopened. Continue wherever you left off."); } }).catch(e => {
      if (!active) return;
      if (e instanceof ApiError && e.status === 404) { setLoaded(true); setMessage("Start with a rough idea. You can save an incomplete draft."); }
      else { setError(e.message); setMessage("Could not open your workspace."); }
    }).finally(() => { if (active) setBusy(false); });
    return () => { active = false; };
  }, []);
  useEffect(() => {
    if (!unsaved) return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [unsaved]);
  const run: Run = async (task, feedback) => {
    setBusy(true); setError(""); setMessage("Working… Your input stays in place.");
    try { await task(); setMessage(feedback ?? "Ready."); return true; }
    catch (e) { setError(e instanceof Error ? e.message : "The request failed. Try again."); setMessage("Request failed. Your input has been preserved."); return false; }
    finally { setBusy(false); }
  };
  const contextChanged = () => { if (proposal) setStale(true); };
  async function save() {
    await run(async () => {
      const data = { description, state, preferences, ...(proposal ? { proposal_context: proposal.proposal_context } : {}) };
      const validation = validateDefinition(data);
      if (validation) throw new Error(validation);
      try { open(await api.save(data)); } catch (e) { if (e instanceof ApiError && e.status === 409 && proposal) setStale(true); throw e; }
    }, state === "ready" ? "Definition saved as ready. You can return and refine it anytime." : "Draft saved. Unknown values can stay open.");
  }
  function discardProposal() { setPreferences(definition?.preferences ?? []); setProposal(null); setStale(false); setMessage("Suggestions discarded. Saved criteria are restored."); }
  return <main id="main-content" className="workspace" tabIndex={-1}>
    <div className="workspace-heading"><div><p className="eyebrow">{t("Your next chapter")}</p><h1>{t("Define your ideal job.")}</h1><p className="lead">{t("Make room for the work you want, and the life around it.")}</p></div><span className="workspace-tag">{t("Personal workspace")}</span></div>
    <aside className="mock-notice" aria-label={t("Mock preview")}><strong>{t("Local preview")}</strong><span>{t("Requests are mocked. Saved work stays in this browser; document extraction and AI suggestions are simulated. No backend or OpenAI calls are made.")}</span></aside>
    <div className="feedback" aria-busy={busy}><p role="status">{t(message)}</p>{error && <p role="alert" className="inline-error">{t(error)}</p>}{!loaded && !busy && <button onClick={() => void run(load)}>{t("Retry opening workspace")}</button>}</div>
    <fieldset className="workspace-controls" disabled={busy || !loaded}>
      <legend className="sr-only">{t("Job definition workspace")}</legend>
      <div className="editor-layout">
        <aside className="sidebar"><nav aria-label={t("Definition steps")}><ol>{steps.map((name, i) => <li key={name}><button type="button" aria-current={step === i ? "step" : undefined} onClick={() => setStep(i)}><span className="step-number">0{i + 1}</span>{t(name)}<span aria-hidden="true" className="step-arrow">↗</span></button></li>)}</ol></nav><div className="sidebar-note"><strong>{t("A direction, not a deadline.")}</strong><p>{t("You can leave things unknown and come back when your priorities change.")}</p></div><div className="save-summary"><span className="badge">{state === "draft" ? t("Draft") : t("Ready")}</span><p>{unsaved ? t("Unsaved changes") : definition ? t("All definition changes saved") : t("No saved definition yet")}</p>{definition && <button type="button" className="text-button" onClick={() => { if (!unsaved || window.confirm(t("Discard unsaved definition edits and reopen the saved definition?"))) void run(load, "Saved definition reopened."); }}>{t("Reopen saved definition")}</button>}</div></aside>
        <div className="editor-content">
          <section hidden={step !== 0} aria-labelledby="describe-title"><p className="section-kicker">{t("01 / Your direction")}</p><h2 id="describe-title">{t("Start with what matters.")}</h2><p className="section-intro">{t("A rough idea is enough. Include the responsibilities you enjoy, compensation, where you want to work, and the balance you need.")}</p><label htmlFor="description">{t("Your ideal job description")}<textarea id="description" rows={10} maxLength={20000} value={description} onChange={e => setDescription(e.target.value)} placeholder={t("I’m looking for a role where I can…")} aria-describedby="description-help" /></label><p id="description-help" className="hint">{t("English or Spanish is welcome.")} {description.length.toLocaleString(locale)}{t("/20,000 characters. Save your first draft before adding background or asking for suggestions.")}</p><div className="actions"><button className="primary" type="button" disabled={stale} onClick={() => void save()}>{proposal ? t("Save reviewed definition") : t("Save draft")}</button><button type="button" disabled={!definition} onClick={() => setStep(1)}>{t("Continue to background")} <span aria-hidden="true">→</span></button></div></section>
          <section hidden={step !== 1} aria-label={t("Background")}>{definition ? <Background api={api} definition={definition} run={run} language={language} onAdded={s => { setDefinition(d => d ? { ...d, sources: [...d.sources, s] } : d); contextChanged(); }} onReviewed={s => { setDefinition(d => d ? { ...d, sources: d.sources.map(old => old.id === s.id ? s : old), clarifications: [] } : d); contextChanged(); }} onRemoved={id => { setDefinition(d => d ? { ...d, sources: d.sources.filter(s => s.id !== id), clarifications: [] } : d); contextChanged(); }} /> : <div className="empty"><h2>{t("Save a starting point first.")}</h2><p>{t("A description is all you need. Background sources are optional.")}</p><button onClick={() => setStep(0)}>{t("Go to description")}</button></div>}</section>
          <section hidden={step !== 2} aria-labelledby="clarify-title"><p className="section-kicker">{t("03 / A little clarity")}</p><h2 id="clarify-title">{t("Make the unknowns useful.")}</h2><p className="section-intro">{t("Review focused questions and suggested criteria. Only accepted background is used; historical skills stay separate from desired work.")}</p><label className="language-control">{t("Assistance language")}<select value={language} onChange={e => setAssistanceOverride(e.target.value as Language)}><option value="English">{t("English")}</option><option value="Spanish">{t("Spanish")}</option></select></label><button className="primary" type="button" disabled={!definition || dirty || Boolean(proposal)} onClick={() => void run(async () => { const result = await api.clarify(language); setProposal(result); setStale(false); setPreferences(result.proposal.preferences); setDefinition(d => d ? { ...d, clarifications: [...d.clarifications, ...result.clarifications] } : d); }, "Suggestions are ready to review. Answer questions here or open Review & save.")}>{t("Request clarification & suggestions")}</button>{!definition || dirty || proposal ? <p className="hint">{!definition ? t("Save an initial draft first.") : proposal ? t("Review and save or discard the current suggestions before requesting another round.") : t("Save your definition edits before requesting suggestions.")}</p> : <p className="hint">{t("Up to three questions per round. Suggestions remain unapplied until you review and save them.")}</p>}
            {proposal && <div className="proposal-callout"><strong>{t("Suggestions awaiting review")}</strong><p>{t("Questions save now; proposed criteria are still unsaved.")}</p><button type="button" onClick={() => setStep(3)}>{t("Review suggested criteria")}</button></div>}
            {definition?.clarifications.length ? definition.clarifications.map(q => <QuestionCard key={q.id} question={q} api={api} run={run} onSaved={updated => { setDefinition(d => d ? { ...d, clarifications: d.clarifications.map(old => old.id === updated.id ? updated : old) } : d); contextChanged(); }} />) : <p className="empty">{t("No clarification questions yet. You can also edit your criteria directly in Review & save.")}</p>}
          </section>
          <section hidden={step !== 3} aria-labelledby="review-title"><p className="section-kicker">{t("04 / Review & save")}</p><h2 id="review-title">{t("Give your next role shape.")}</h2><p className="section-intro">{t("Mandatory criteria are firm constraints. Preferred criteria are flexible; excluded criteria describe work you want to avoid. Blank or unknown values are valid.")}</p>
            {proposal && <div className="proposal-callout"><strong>{stale ? t("The suggestion context has changed") : t("Review these suggestions before applying")}</strong><p>{stale ? t("Your edited criteria are still here. Request fresh suggestions after discarding this set, or explicitly keep the current criteria as manual edits.") : t("Edit or remove any proposed criterion. Saving applies the complete reviewed definition.")}</p>{proposal.proposal.conflicts.map((conflict, i) => <p className="inline-error" key={i}>{conflict}</p>)}<div className="actions"><button type="button" onClick={discardProposal}>{t("Discard suggestions")}</button>{stale && <button type="button" onClick={() => { setProposal(null); setStale(false); setMessage("Criteria kept as unsaved manual edits. Review them before saving."); }}>{t("Keep as manual edits")}</button>}</div></div>}
            <div className="criteria-list">{preferences.length === 0 && <p className="empty">{t("No criteria yet. Add one yourself, or request clarification to explore what matters.")}</p>}{preferences.map((p, i) => <PreferenceEditor key={i} index={i} preference={p} onChange={updated => setPreferences(current => current.map((old, n) => n === i ? updated : old))} onRemove={() => setPreferences(current => current.filter((_, n) => n !== i))} />)}</div>
            <button type="button" disabled={preferences.length >= 100} onClick={() => setPreferences(current => [...current, newPreference(current)])}>{t("+ Add criterion")}</button>
            <div className="save-panel"><label>{t("Definition status")}<select value={state} onChange={e => setState(e.target.value as typeof state)}><option value="draft">{t("Draft — still exploring")}</option><option value="ready">{t("Ready — my current direction")}</option></select></label><p className="hint">{t("You decide when it is ready. You can refine either status later.")}</p><p className="unsaved-indicator">{unsaved ? t("Unsaved changes") : t("No unsaved definition changes")}</p><button className="primary" type="button" disabled={stale} onClick={() => void save()}>{proposal ? t("Apply reviewed suggestions & save") : t("Save definition")}</button></div>
            {definition && <details className="delete-section"><summary>{t("Delete this definition")}</summary><p>{t("This removes the definition, sources, background facts, and clarification answers. Original files are queued for deletion. Backup copies expire within seven days.")}</p>{!confirmDelete ? <button type="button" className="danger" onClick={() => setConfirmDelete(true)}>{t("Delete definition and sources")}</button> : <div className="confirmation"><p>{t("Delete all current work? This cannot be undone.")}</p><div className="actions"><button type="button" className="danger" onClick={() => void run(async () => { await api.remove(); open(null); setConfirmDelete(false); setStep(0); }, "Definition and its sources deleted.")}>{t("Confirm delete definition")}</button><button type="button" onClick={() => setConfirmDelete(false)}>{t("Cancel deletion")}</button></div></div>}</details>}
          </section>
        </div>
      </div>
    </fieldset>
  </main>;
}
