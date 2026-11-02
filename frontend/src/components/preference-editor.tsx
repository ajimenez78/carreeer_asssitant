import { useI18n } from "../lib/i18n/provider";
import type { Compensation, OnsiteLimit, Preference, PreferenceValue } from "../lib/contracts";
import { categories } from "../lib/contracts";
import { emptyCompensation, emptyOnsite, label, valueType } from "../lib/preferences";

export function PreferenceEditor({ preference: p, index, onChange, onRemove }: { preference: Preference; index: number; onChange: (p: Preference) => void; onRemove: () => void }) {
  const { t } = useI18n();
  const type = valueType(p.value);
  const changeValue = (value: PreferenceValue) => onChange({ ...p, value });
  const prefix = `criterion-${index}`;
  const types = p.category === "compensation" ? ["unknown", "compensation"] : ["unknown", "string", "number", "boolean", "list", ...(p.category === "work_arrangement" ? ["onsite"] : [])];
  const names: Record<string, string> = { unknown: "Unknown", string: "Text", number: "Number", boolean: "Yes / No", list: "Text list", compensation: "Compensation range", onsite: "On-site limit" };
  const defaults: Record<string, PreferenceValue> = { unknown: null, string: "", number: 0, boolean: true, list: [], compensation: { ...emptyCompensation }, onsite: { ...emptyOnsite } };
  return (
    <fieldset className="criterion">
      <legend>{t("Criterion")} {index + 1}</legend>
      <div className="form-grid">
        <label htmlFor={`${prefix}-name`}>{t("Criterion name")}<input id={`${prefix}-name`} maxLength={80} value={p.key} onChange={e => onChange({ ...p, key: e.target.value })} /></label>
        <label htmlFor={`${prefix}-category`}>{t("Category")}<select id={`${prefix}-category`} value={p.category} onChange={e => onChange({ ...p, category: e.target.value as Preference["category"], value: e.target.value === "compensation" || type === "compensation" || type === "onsite" ? null : p.value })}>{categories.map(c => <option key={c} value={c}>{t(label(c))}</option>)}</select></label>
        <label htmlFor={`${prefix}-priority`}>{t("Priority")}<select id={`${prefix}-priority`} value={p.priority} onChange={e => onChange({ ...p, priority: e.target.value as Preference["priority"] })}><option value="mandatory">{t("Mandatory")}</option><option value="preferred">{t("Preferred")}</option><option value="excluded">{t("Excluded")}</option></select></label>
        <label htmlFor={`${prefix}-type`}>{t("Value type")}<select id={`${prefix}-type`} value={type} onChange={e => changeValue(defaults[e.target.value])}>{types.map(kind => <option key={kind} value={kind}>{t(names[kind])}</option>)}</select></label>
      </div>
      {p.value === null && <p className="hint unknown">{t("Unknown — leave this open until you decide.")}</p>}
      {type === "string" && <label>{t("Value")}<textarea maxLength={4000} value={p.value as string} onChange={e => changeValue(e.target.value)} rows={2} /></label>}
      {type === "number" && <label>{t("Value")}<input type="number" step="any" value={p.value as number} onChange={e => changeValue(e.target.value === "" ? null : Number(e.target.value))} /></label>}
      {type === "boolean" && <label>{t("Value")}<select value={String(p.value)} onChange={e => changeValue(e.target.value === "true")}><option value="true">{t("Yes")}</option><option value="false">{t("No")}</option></select></label>}
      {type === "list" && <label>{t("Values, one per line")}<textarea value={(p.value as string[]).join("\n")} onChange={e => changeValue(e.target.value.split("\n"))} rows={3} /></label>}
      {type === "compensation" && <CompensationFields value={p.value as Compensation} onChange={changeValue} />}
      {type === "onsite" && <OnsiteFields value={p.value as OnsiteLimit} onChange={changeValue} />}
      <label>{t("Condition or note")} <span className="optional">{t("(optional)")}</span><textarea maxLength={2000} rows={2} value={p.note ?? ""} onChange={e => onChange({ ...p, note: e.target.value || null })} placeholder={t("For example: this limit applies if the role is hybrid.")} /></label>
      <button className="text-button danger" type="button" onClick={onRemove}>{t("Remove criterion")} {index + 1}</button>
    </fieldset>
  );
}

function CompensationFields({ value: v, onChange }: { value: Compensation; onChange: (v: Compensation) => void }) {
  const { t } = useI18n();
  return <fieldset className="value-fields"><legend>{t("Compensation details")}</legend><p className="hint">{t("Blank fields remain unknown. No currency or pay period is assumed.")}</p><div className="form-grid">
    {(["minimum", "maximum", "target"] as const).map(key => <label key={key}>{t(label(key))}<input type="number" min={0} step="any" value={v[key] ?? ""} onChange={e => onChange({ ...v, [key]: e.target.value === "" ? null : Number(e.target.value) })} /></label>)}
    <label>{t("Currency")}<input maxLength={3} placeholder={t("Unknown")} value={v.currency ?? ""} onChange={e => onChange({ ...v, currency: e.target.value.toUpperCase() || null })} /></label>
    <label>{t("Pay period")}<select value={v.period ?? ""} onChange={e => onChange({ ...v, period: (e.target.value || null) as Compensation["period"] })}><option value="">{t("Unknown")}</option>{["hour", "day", "week", "month", "year"].map(x => <option key={x} value={x}>{t(`Per ${x}`)}</option>)}</select></label>
    <label>{t("Tax basis")}<select value={v.basis ?? ""} onChange={e => onChange({ ...v, basis: (e.target.value || null) as Compensation["basis"] })}><option value="">{t("Unknown")}</option><option value="gross">{t("Gross")}</option><option value="net">{t("Net")}</option></select></label>
  </div></fieldset>;
}
function OnsiteFields({ value: v, onChange }: { value: OnsiteLimit; onChange: (v: OnsiteLimit) => void }) {
  const { t } = useI18n();
  return <div className="form-grid"><label>{t("Maximum on-site days")}<input type="number" min={0} max={366} step={1} placeholder={t("Unknown")} value={v.days ?? ""} onChange={e => onChange({ ...v, days: e.target.value === "" ? null : Number(e.target.value) })} /></label><label>{t("On-site period")}<select value={v.period ?? ""} onChange={e => onChange({ ...v, period: (e.target.value || null) as OnsiteLimit["period"] })}><option value="">{t("Unknown")}</option>{["week", "month", "year"].map(x => <option key={x} value={x}>{t(`Per ${x}`)}</option>)}</select></label></div>;
}
