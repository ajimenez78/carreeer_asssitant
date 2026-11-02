import { useEffect, useRef, useState } from "react";
import type { Client } from "../lib/client";
import type { ChatHistory, ChatTurn, Definition, Language } from "../lib/contracts";
import { useI18n } from "../lib/i18n/provider";
import type { Run } from "./background";

export function Chat({ api, definitionId, active, history, onHistory, language, setLanguage, run, blockedReason, disabled, error, unsaved, onStart, onResponse, onReview }: {
  api: Client; definitionId: string | null; active: boolean; history: ChatHistory | null;
  onHistory: (history: ChatHistory) => void; language: Language; setLanguage: (language: Language) => void;
  run: Run; blockedReason: string | null; disabled: boolean; error: string; unsaved: boolean; onStart: (definition: Definition) => void; onResponse: () => void; onReview: (turn: ChatTurn) => void;
}) {
  const { t } = useI18n();
  const [message, setMessage] = useState("");
  const pending = useRef<{ id: string; message: string; language: Language } | null>(null);
  const previousDefinition = useRef(definitionId);
  const transcript = useRef<HTMLDivElement>(null);
  const [loadError, setLoadError] = useState(false);
  useEffect(() => {
    if (previousDefinition.current !== definitionId) {
      const previous = previousDefinition.current;
      previousDefinition.current = definitionId;
      if (previous !== null) { pending.current = null; setMessage(""); }
      setLoadError(false);
    }
  }, [definitionId]);
  // Reads resume persisted conversation; only the Send action calls the model.
  useEffect(() => {
    if (!active || !definitionId || history || loadError) return;
    let canceled = false;
    api.chat().then(result => { if (!canceled) onHistory(result); })
      .catch(() => { if (!canceled) setLoadError(true); });
    return () => { canceled = true; };
  }, [api, active, definitionId, history, onHistory, loadError]);

  useEffect(() => {
    if (active && transcript.current) transcript.current.scrollTop = transcript.current.scrollHeight;
  }, [active, history?.turns.length]);

  async function send() {
    if (disabled || blockedReason || definitionId && !history || !message.trim()) return;
    const text = message.trim();
    if (!pending.current || pending.current.message !== text || pending.current.language !== language)
      pending.current = { id: crypto.randomUUID(), message: text, language };
    const id = pending.current.id;
    await run(async () => {
      if (!definitionId) {
        const draft = await api.save({ description: text, state: "draft", preferences: [] });
        onStart(draft);
      }
      const turn = await api.sendChat(text, language, id);
      onHistory({ turns: [...(history?.turns ?? []).filter(old => old.id !== turn.id), turn], context: turn.proposal_context });
      if (turn.in_scope) onResponse();
      pending.current = null; setMessage("");
    }, "Chat reply saved. Review any proposed changes before applying them.");
  }
  return <>
    <p className="hint">{t("Discuss your role from any step. Proposed changes always need your review.")}</p>
    {!definitionId && <p className="empty">{t("Your first message starts a saved role draft. Any description edits stay in the editor until you save them.")}</p>}
    <fieldset className="workspace-controls assistant-conversation" disabled={disabled} aria-busy={disabled}>
      <legend className="sr-only">{t("Assistant conversation")}</legend>
      {loadError && <div role="alert"><p>{t("Could not open the conversation. Retry to continue.")}</p><button type="button" onClick={() => setLoadError(false)}>{t("Retry conversation")}</button></div>}
      {definitionId && !history && !loadError && <p>{t("Opening conversation…")}</p>}
      {history && <div className="chat-history" ref={transcript} aria-label={t("Saved conversation")}>
        {!history.turns.length && <p className="empty">{t("No messages yet. Tell the assistant what you would like to clarify or change.")}</p>}
        {history.turns.map(turn => <article className="chat-turn" key={turn.id}>
          <h3>{t("You")}</h3><p className="chat-prose">{turn.message}</p>
          <h3>{t("Assistant")}</h3><p className="chat-prose">{turn.reply}</p>
          {turn.questions.length > 0 && <ul>{turn.questions.map((q, i) => <li key={i}>{q}</li>)}</ul>}
          {turn.has_changes && <div className="proposal-callout"><strong>{t(turn.proposal_context === history.context ? "Proposed changes · not applied" : "Earlier proposal")}</strong>
            {turn.proposal.conflicts.map((c, i) => <p key={i}>{c}</p>)}
            {turn.proposal_context === history.context ? <button type="button" disabled={Boolean(blockedReason) || unsaved} onClick={() => onReview(turn)}>{t("Review chat suggestions")}</button> : <p>{t("The saved context has changed. Send a new message for current suggestions.")}</p>}
          </div>}
        </article>)}
      </div>}
      <label className="language-control">{t("Chat reply language")}<select value={language} onChange={e => setLanguage(e.target.value as Language)}><option value="English">{t("English")}</option><option value="Spanish">{t("Spanish")}</option></select></label>
      <label htmlFor="chat-message">{t("Your message")}</label><textarea id="chat-message" rows={3} maxLength={4000} value={message} aria-describedby={error ? "chat-error" : undefined} onChange={e => setMessage(e.target.value)} />
      {unsaved && definitionId && <p className="hint">{t("Chat uses your saved role. Your unsaved edits are preserved. Save or discard them before reviewing chat suggestions.")}</p>}
      {error && <p id="chat-error" className="inline-error">{t(error)}</p>}
      {blockedReason && <p className="hint">{t(blockedReason)}</p>}
      <button className="primary" type="button" disabled={Boolean(blockedReason) || Boolean(definitionId && !history) || !message.trim()} onClick={() => void send()}>{t("Send message")}</button>
    </fieldset>
  </>;
}
