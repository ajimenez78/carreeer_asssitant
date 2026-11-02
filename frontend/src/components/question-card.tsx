import { useI18n } from "../lib/i18n/provider";
import { useState } from "react";
import type { Client } from "../lib/client";
import type { Question } from "../lib/contracts";
import type { Run } from "./background";
export function QuestionCard({ question: q, api, run, onSaved }: { question: Question; api: Client; run: Run; onSaved: (q: Question) => void }) {
  const { t } = useI18n();
  const [answer, setAnswer] = useState(q.answer ?? "");
  const id = `answer-${q.id}`;
  return <article className="card question-card">
    <span className="badge">{q.answer_state === "unanswered" ? t("Open question") : q.answer_state === "answered" ? t("Answer saved") : q.answer_state === "skipped" ? t("Skipped") : t("Explicitly unknown")}</span>
    <label htmlFor={id}>{q.question}<textarea id={id} rows={3} maxLength={4000} value={answer} onChange={e => setAnswer(e.target.value)} /></label>
    <div className="actions"><button type="button" className="primary" onClick={() => void run(async () => { if (!answer.trim()) throw new Error("Enter an answer, skip this question, or mark it unknown."); onSaved(await api.answer(q.id, "answered", answer)); }, "Answer saved. Request suggestions again when ready to review its effect.")}>{t("Save answer")}</button><button type="button" onClick={() => void run(async () => onSaved(await api.answer(q.id, "skipped")), "Question skipped; no value was invented.")}>{t("Skip question")}</button><button type="button" onClick={() => void run(async () => onSaved(await api.answer(q.id, "unknown")), "Answer marked unknown.")}>{t("I don’t know yet")}</button></div>
    <p className="hint">{t("Answers save independently. They do not apply job criteria automatically.")}</p>
  </article>;
}
