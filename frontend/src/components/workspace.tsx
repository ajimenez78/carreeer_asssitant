"use client";

import { useI18n } from "../lib/i18n/provider";
import { locales } from "../lib/i18n/catalogs";

import { useEffect, useRef, useState } from "react";
import { ApiError } from "../lib/client";
import type { ClarificationProposal, Definition, Language, Preference } from "../lib/contracts";
import { api, MOCK_MODE } from "../lib/runtime-client";
import { useSession } from "./session-gate";
import { newPreference, validateDefinition } from "../lib/preferences";
import { Background, type Run } from "./background";
import { PreferenceEditor } from "./preference-editor";
import { QuestionCard } from "./question-card";
import { SummaryView } from "./summary-view";

const steps = ["Describe", "Background", "Clarify", "Review & save", "Summary"];

export function Workspace() {
  const { t, locale } = useI18n();
  const session = useSession();
  const [definition, setDefinition] = useState<Definition | null>(null);
  const [description, setDescription] = useState("");
  const [preferences, setPreferences] = useState<Preference[]>([]);
  const [step, setStep] = useState(0);
  const [assistanceOverride, setAssistanceOverride] = useState<Language | null>(null);
  const language: Language = assistanceOverride ?? locales[locale].assistanceLanguage;
  const [proposal, setProposal] = useState<ClarificationProposal | null>(null);
  const [staleContext, setStaleContext] = useState<string | null>(null);
  const stale = proposal !== null && staleContext === proposal.proposal_context;
  const [busy, setBusy] = useState(true);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("Opening your workspace…");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [cleanupPending, setCleanupPending] = useState(false);
  const [pausePending, setPausePending] = useState(false);
  const [localStop, setLocalStop] = useState(false);
  const operation = useRef(0);
  const feedback = useRef(0);
  const clarificationRequest = useRef<AbortController | null>(null);
  const controlGeneration = useRef(0);
  const acknowledgedControl = useRef<{ generation: number; definitionId: string; paused: boolean } | null>(null);
  const paused = localStop || Boolean(definition?.clarification_paused);
  const dirty = description !== (definition?.description ?? "") || JSON.stringify(preferences) !== JSON.stringify(definition?.preferences ?? []);
  const unsaved = dirty || proposal !== null;
  const assessmentLabel = definition?.assessment ? definition.assessment.sufficient ? "Sufficiently clear" : "Needs clarification" : "Not assessed yet";
  const assessmentBlocked = !definition ? "Save an initial draft first." : paused ? "Clarification is stopped. Resume when you want to continue." : pausePending ? "Wait for the clarification control to finish." : proposal ? "Review and save or discard the current suggestions before requesting another round." : dirty ? "Save your definition edits before requesting suggestions." : null;

  function open(d: Definition | null, acknowledgedAtStart?: number) {
    const control = acknowledgedControl.current;
    // Keep a control acknowledged while this read/write was pending. Requests
    // started after that acknowledgment still reopen the server's current truth.
    const current = d && acknowledgedAtStart !== undefined && control && control.generation > acknowledgedAtStart && control.definitionId === d.id
      ? { ...d, clarification_paused: control.paused }
      : d;
    setDefinition(current); setDescription(current?.description ?? ""); setPreferences(current?.preferences ?? []); setProposal(null); setStaleContext(null);
    if (!d) setLocalStop(false);
  }
  async function load() {
    const acknowledgedAtStart = acknowledgedControl.current?.generation ?? 0;
    try { const d = await api.read(); open(d, acknowledgedAtStart); }
    catch (e) { if (e instanceof ApiError && e.status === 404) open(null); else throw e; }
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
    if (!unsaved && !localStop) return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [unsaved, localStop]);
  useEffect(() => () => { clarificationRequest.current?.abort(); }, []);
  const run: Run = async (task, successMessage) => {
    const currentOperation = ++operation.current;
    const currentFeedback = ++feedback.current;
    setBusy(true); setError(""); setMessage("Working… Your input stays in place.");
    try { await task(); if (feedback.current === currentFeedback) setMessage(successMessage ?? "Ready."); return true; }
    catch (e) { if (operation.current === currentOperation) { ++feedback.current; setError(e instanceof Error ? e.message : "The request failed. Try again."); setMessage("Request failed. Your input has been preserved."); } return false; }
    finally { if (operation.current === currentOperation) setBusy(false); }
  };
  const contextChanged = () => {
    setDefinition(d => d ? { ...d, assessment: null, state: "draft" } : d);
    if (proposal) setStaleContext(proposal.proposal_context);
  };
  async function assess() {
    if (assessmentBlocked) return;
    const controller = new AbortController();
    clarificationRequest.current = controller;
    const currentOperation = ++operation.current;
    const currentFeedback = ++feedback.current;
    setBusy(true); setError(""); setMessage("Assessing your saved definition… You can stop clarification at any time.");
    try {
      const result = await api.clarify(language, controller.signal);
      if (operation.current !== currentOperation || controller.signal.aborted) return;
      setProposal(result); setStaleContext(null); setPreferences(result.proposal.preferences);
      setDefinition(d => d ? { ...d, assessment: result.assessment, state: result.state, clarifications: [...d.clarifications, ...result.clarifications] } : d);
      if (feedback.current === currentFeedback) setMessage("Your saved definition has been assessed. Review its summary and any suggested criteria.");
    } catch (e) {
      if (operation.current !== currentOperation || controller.signal.aborted) return;
      if (feedback.current === currentFeedback) { setError(e instanceof Error ? e.message : "The request failed. Try again."); setMessage("Request failed. Your input has been preserved."); }
    } finally {
      if (operation.current === currentOperation) { clarificationRequest.current = null; setBusy(false); }
    }
  }
  async function controlClarification(stop: boolean) {
    if (!definition || pausePending) return;
    const definitionId = definition.id;
    const generation = ++controlGeneration.current;
    if (stop) {
      setLocalStop(true);
      if (clarificationRequest.current) {
        clarificationRequest.current.abort(); clarificationRequest.current = null;
        ++operation.current; setBusy(false);
      }
    }
    const currentFeedback = ++feedback.current;
    setPausePending(true); setError(""); setMessage(stop ? "Saving your choice to stop clarification…" : "Resuming clarification…");
    try {
      const result = await api.controlClarification(stop);
      acknowledgedControl.current = { generation, definitionId, paused: result.clarification_paused };
      setDefinition(d => d?.id === definitionId ? { ...d, clarification_paused: result.clarification_paused } : d);
      if (proposal) setStaleContext(proposal.proposal_context);
      setLocalStop(false);
      if (feedback.current === currentFeedback) setMessage(stop ? "Clarification stopped. Your saved work and unsaved input are preserved." : "Clarification resumed. Request an assessment when you’re ready.");
    } catch (e) {
      if (feedback.current === currentFeedback) {
        setError(e instanceof Error ? e.message : "The request failed. Try again.");
        setMessage(stop ? "Clarification was canceled here, but stopping could not be saved. Retry stopping before leaving." : "Clarification could not be resumed. Your input is preserved.");
      }
    } finally { setPausePending(false); }
  }
  async function save() {
    const acknowledgedAtStart = acknowledgedControl.current?.generation ?? 0;
    await run(async () => {
      const data = { description, state: definition?.state ?? "draft", preferences, ...(proposal ? { proposal_context: proposal.proposal_context } : {}) };
      const validation = validateDefinition(data);
      if (validation) throw new Error(validation);
      try { open(await api.save(data), acknowledgedAtStart); } catch (e) { if (e instanceof ApiError && e.status === 409 && proposal) setStaleContext(proposal.proposal_context); throw e; }
    }, "Definition saved.");
  }
  function discardProposal() { setPreferences(definition?.preferences ?? []); setProposal(null); setStaleContext(null); setMessage("Suggestions discarded. Saved criteria are restored."); }
  return <div className="workspace">
    <div className="workspace-heading"><div><p className="eyebrow">{t("Your next chapter")}</p><h1>{t("Clarify the role you’re looking for.")}</h1><p className="lead">{t("Explore the work you’re looking for and how it fits your life.")}</p></div><span className="workspace-tag">{t("Personal workspace")}</span></div>
    {session && <button type="button" disabled={busy} onClick={() => { if (!unsaved || window.confirm(t("Sign out and discard unsaved definition edits?"))) void run(session.signOut); }}>{t("Sign out")}</button>}
    {MOCK_MODE && <aside className="mock-notice" aria-label={t("Mock preview")}><strong>{t("Local preview")}</strong><span>{t("Requests are mocked. Saved work stays in this browser; document extraction and AI suggestions are simulated. No backend or OpenAI calls are made.")}</span></aside>}
    <div className="feedback" aria-busy={busy}><p role="status">{t(message)}</p>{error && <p role="alert" className="inline-error">{t(error)}</p>}{!loaded && !busy && <button onClick={() => void run(load)}>{t("Retry opening workspace")}</button>}</div>
    {definition && <aside className="clarification-controls" aria-label={t("Clarification controls")}>
      <div><strong>{paused ? t("Clarification is stopped") : t("The system assesses clarity")}</strong><p>{paused ? t("Your definition remains editable. Resume whenever you want another assessment.") : t("The assistant checks whether your saved role is clear enough and helps you explore what is missing. You can stop at any time.")}</p>{localStop && !pausePending && <p className="inline-error">{t("Stopping has not been saved. Retry before leaving to keep clarification stopped when you return.")}</p>}</div>
      <button type="button" disabled={pausePending || (!paused && !loaded) || (paused && busy)} onClick={() => void controlClarification(!paused || localStop)}>{pausePending ? t("Saving choice…") : localStop ? t("Retry stopping") : paused ? t("Resume clarification") : t("Stop clarification")}</button>
    </aside>}
    {cleanupPending && <aside className="proposal-callout"><p>{t("Source records were removed, but original-file cleanup is still pending.")}</p><button type="button" disabled={busy} onClick={() => void run(async () => setCleanupPending((await api.cleanup()).cleanup_pending), "Cleanup retried.")}>{t("Retry original cleanup")}</button></aside>}
    <fieldset className="workspace-controls" disabled={busy || !loaded}>
      <legend className="sr-only">{t("Job definition workspace")}</legend>
      <div className="editor-layout">
        <aside className="sidebar"><nav aria-label={t("Definition steps")}><ol>{steps.map((name, i) => <li key={name}><button type="button" aria-current={step === i ? "step" : undefined} onClick={() => setStep(i)}><span className="step-number">0{i + 1}</span>{t(name)}<span aria-hidden="true" className="step-arrow">↗</span></button></li>)}</ol></nav><div className="sidebar-note"><strong>{t("A direction, not a deadline.")}</strong><p>{t("You can leave things unknown and come back when your priorities change.")}</p></div><div className="save-summary"><span className="badge">{t(assessmentLabel)}</span>{paused && <span className="badge">{t("Clarification stopped")}</span>}<p>{unsaved ? t("Unsaved changes") : definition ? t("All definition changes saved") : t("No saved definition yet")}</p>{definition && <button type="button" className="text-button" onClick={() => { if (!unsaved || window.confirm(t("Discard unsaved definition edits and reopen the saved definition?"))) void run(load, "Saved definition reopened."); }}>{t("Reopen saved definition")}</button>}</div></aside>
        <div className="editor-content">
          <section hidden={step !== 0} aria-labelledby="describe-title"><p className="section-kicker">{t("01 / Your direction")}</p><h2 id="describe-title">{t("Start with what matters.")}</h2><p className="section-intro">{t("A rough idea is enough. Include the responsibilities you enjoy, compensation, where you want to work, and the balance you need.")}</p><label htmlFor="description">{t("The role you’re looking for")}<textarea id="description" rows={10} maxLength={20000} value={description} onChange={e => setDescription(e.target.value)} placeholder={t("I’m looking for a role where I can…")} aria-describedby="description-help" /></label><p id="description-help" className="hint">{t("English or Spanish is welcome.")} {description.length.toLocaleString(locale)}{t("/20,000 characters. Save your first draft before adding background or asking for suggestions.")}</p><div className="actions"><button className="primary" type="button" disabled={stale} onClick={() => void save()}>{proposal ? t("Save reviewed definition") : t("Save draft")}</button><button type="button" disabled={!definition} onClick={() => setStep(1)}>{t("Continue to background")} <span aria-hidden="true">→</span></button></div></section>
          <section hidden={step !== 1} aria-label={t("Background")}>{definition ? <Background api={api} definition={definition} run={run} language={language} onCleanup={result => setCleanupPending(result.cleanup_pending)} onAdded={s => { setDefinition(d => d ? { ...d, sources: [...d.sources, s], clarifications: [] } : d); contextChanged(); }} onReviewed={s => { setDefinition(d => d ? { ...d, sources: d.sources.map(old => old.id === s.id ? s : old), clarifications: [] } : d); contextChanged(); }} onRemoved={id => { setDefinition(d => d ? { ...d, sources: d.sources.filter(s => s.id !== id), clarifications: [] } : d); contextChanged(); }} /> : <div className="empty"><h2>{t("Save a starting point first.")}</h2><p>{t("A description is all you need. Background sources are optional.")}</p><button onClick={() => setStep(0)}>{t("Go to description")}</button></div>}</section>
          <section hidden={step !== 2} aria-labelledby="clarify-title"><p className="section-kicker">{t("03 / A little clarity")}</p><h2 id="clarify-title">{t("Make the unknowns useful.")}</h2><p className="section-intro">{t("Review focused questions and suggested criteria. Only accepted background is used; historical skills stay separate from desired work.")}</p>
            <div className="clarity-status"><strong>{t(assessmentLabel)}</strong><p>{definition?.assessment ? definition.assessment.explanation : t("Request an assessment to see whether your saved definition is clear enough and what would help clarify it.")}</p>{definition?.assessment && <p className="hint">{definition.assessment.sufficient ? t("Your saved role is sufficiently clear. You can review suggestions or refine it when your preferences change.") : t("Answer the useful questions, review suggested criteria, and save the changes you accept. Then request another assessment. You may skip questions or leave values unknown.")}</p>}<button type="button" className="text-button" onClick={() => setStep(4)}>{t("View role summary")}</button></div>
            <label className="language-control">{t("Assistance language")}<select value={language} onChange={e => setAssistanceOverride(e.target.value as Language)}><option value="English">{t("English")}</option><option value="Spanish">{t("Spanish")}</option></select></label><button className="primary" type="button" disabled={Boolean(assessmentBlocked)} onClick={() => void assess()}>{t("Request clarification & suggestions")}</button><p className="hint">{assessmentBlocked ? t(assessmentBlocked) : t("Up to three questions per round. Suggestions remain unapplied until you review and save them.")}</p>
            {proposal && <div className="proposal-callout"><strong>{t("Suggestions awaiting review")}</strong><p>{t("Questions save now; proposed criteria are still unsaved.")}</p><button type="button" onClick={() => setStep(3)}>{t("Review suggested criteria")}</button></div>}
            {definition?.clarifications.length ? definition.clarifications.map(q => <QuestionCard key={q.id} question={q} api={api} run={run} onSaved={updated => { setDefinition(d => d ? { ...d, clarifications: d.clarifications.map(old => old.id === updated.id ? updated : old) } : d); contextChanged(); }} />) : <p className="empty">{t("No clarification questions yet. You can also edit your criteria directly in Review & save.")}</p>}
          </section>
          <section hidden={step !== 3} aria-labelledby="review-title"><p className="section-kicker">{t("04 / Review & save")}</p><h2 id="review-title">{t("Bring the role you’re looking for into focus.")}</h2><p className="section-intro">{t("Mandatory criteria are firm constraints. Preferred criteria are flexible; excluded criteria describe work you want to avoid. Blank or unknown values are valid.")}</p>
            {proposal && <div className="proposal-callout"><strong>{stale ? t("The suggestion context has changed") : t("Review these suggestions before applying")}</strong><p>{stale ? t("Your edited criteria are still here. Request fresh suggestions after discarding this set, or explicitly keep the current criteria as manual edits.") : t("Edit or remove any proposed criterion. Saving applies the complete reviewed definition.")}</p>{proposal.proposal.conflicts.map((conflict, i) => <p className="inline-error" key={i}>{conflict}</p>)}<div className="actions"><button type="button" onClick={discardProposal}>{t("Discard suggestions")}</button>{stale && <button type="button" onClick={() => { setProposal(null); setStaleContext(null); setMessage("Criteria kept as unsaved manual edits. Review them before saving."); }}>{t("Keep as manual edits")}</button>}</div></div>}
            <div className="criteria-list">{preferences.length === 0 && <p className="empty">{t("No criteria yet. Add one yourself, or request clarification to explore what matters.")}</p>}{preferences.map((p, i) => <PreferenceEditor key={i} index={i} preference={p} onChange={updated => setPreferences(current => current.map((old, n) => n === i ? updated : old))} onRemove={() => setPreferences(current => current.filter((_, n) => n !== i))} />)}</div>
            <button type="button" disabled={preferences.length >= 100} onClick={() => setPreferences(current => [...current, newPreference(current)])}>{t("+ Add criterion")}</button>
            <div className="save-panel"><p><strong>{t("System assessment:")}</strong> {t(assessmentLabel)}</p><p className="hint">{t("The system assesses your saved definition. Saving changes may require a fresh assessment; you can stop clarification without losing your work.")}</p><p className="unsaved-indicator">{unsaved ? t("Unsaved changes") : t("No unsaved definition changes")}</p><button className="primary" type="button" disabled={stale} onClick={() => void save()}>{proposal ? t("Apply reviewed suggestions & save") : t("Save definition")}</button></div>
            {definition && <details className="delete-section"><summary>{t("Delete this definition")}</summary><p>{t("This removes the definition, sources, background facts, and clarification answers. Original files are queued for deletion. Backup copies expire within seven days.")}</p>{!confirmDelete ? <button type="button" className="danger" onClick={() => setConfirmDelete(true)}>{t("Delete definition and sources")}</button> : <div className="confirmation"><p>{t("Delete all current work? This cannot be undone.")}</p><div className="actions"><button type="button" className="danger" onClick={() => void run(async () => { const cleanup = await api.remove(); open(null); setCleanupPending(cleanup.cleanup_pending); setConfirmDelete(false); setStep(0); }, "Definition and its sources deleted.")}>{t("Confirm delete definition")}</button><button type="button" onClick={() => setConfirmDelete(false)}>{t("Cancel deletion")}</button></div></div>}</details>}
          </section>
          <section hidden={step !== 4} aria-labelledby="summary-title"><SummaryView definition={definition} unsaved={unsaved} blockedReason={assessmentBlocked} onAssess={() => void assess()} /></section>
        </div>
      </div>
    </fieldset>
  </div>;
}
