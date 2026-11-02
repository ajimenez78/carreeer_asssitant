import type { Definition } from "../lib/contracts";
import { useI18n } from "../lib/i18n/provider";

export function SummaryView({ definition, unsaved, blockedReason, onAssess }: {
  definition: Definition | null;
  unsaved: boolean;
  blockedReason: string | null;
  onAssess: () => void;
}) {
  const { t, locale } = useI18n();
  const assessment = definition?.assessment;
  const contentLanguage = assessment?.language === "Spanish" ? "es" : "en";

  return <>
    <p className="section-kicker">{t("05 / Your role at a glance")}</p>
    <h2 id="summary-title">{t("The role you’re looking for, in words.")}</h2>
    <p className="section-intro">{t("A natural-language overview of your saved definition, including what is clear and what is still open.")}</p>
    {unsaved && <p className="proposal-callout">{t("This view describes your saved definition. Unsaved edits and proposed criteria are not included until you review and save them.")}</p>}
    {assessment ? <>
      <article className="card role-summary" aria-label={t("Saved role summary")}>
        <span className="badge">{assessment.sufficient ? t("Sufficiently clear") : t("Needs clarification")}</span>
        <p className="summary-prose" lang={contentLanguage}>{assessment.summary}</p>
        <p className="hint">{t("Summary language:")} {t(assessment.language)} · {t("Assessed:")} {new Date(assessment.assessed_at).toLocaleString(locale)}</p>
      </article>
      <div className="clarity-status">
        <h3>{t("Why this assessment?")}</h3>
        <p lang={contentLanguage}>{assessment.explanation}</p>
        {assessment.gaps.length > 0 && <><h3>{t("Still to clarify")}</h3><ul lang={contentLanguage}>{assessment.gaps.map((gap, i) => <li key={i}>{gap}</li>)}</ul></>}
        <p className="hint">{t("Unknown values can remain open. Stopping clarification preserves the current assessment and does not mark the role as sufficiently clear.")}</p>
      </div>
    </> : <p className="empty">{definition ? t("Your saved definition needs a current assessment before its summary can be shown. Request one when you want to continue.") : t("Save a starting description to get a summary of the role you’re looking for.")}</p>}
    <button type="button" className="primary" disabled={Boolean(blockedReason)} onClick={onAssess}>{t("Assess clarity & update summary")}</button>
    {blockedReason && <p className="hint">{t(blockedReason)}</p>}
  </>;
}
