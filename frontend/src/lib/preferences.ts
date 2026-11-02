import type { Compensation, OnsiteLimit, Preference, PreferenceValue, SaveDefinition } from "./contracts";
export const label = (key: string) => key.replaceAll("_", " ").replace(/^./, c => c.toUpperCase());
export const emptyCompensation: Compensation = { minimum: null, maximum: null, target: null, currency: null, period: null, basis: null };
export const emptyOnsite: OnsiteLimit = { days: null, period: null };
function serializedValue(value: PreferenceValue): string {
  // Match the backend's JSON separators without modifying punctuation in text.
  if (Array.isArray(value)) return `[${value.map(v => JSON.stringify(v)).join(", ")}]`;
  if (value !== null && typeof value === "object") return `{${Object.entries(value).map(([key, v]) => `${JSON.stringify(key)}: ${JSON.stringify(v)}`).join(", ")}}`;
  return JSON.stringify(value);
}
export function valueType(value: PreferenceValue): string {
  if (value === null) return "unknown";
  if (Array.isArray(value)) return "list";
  if (typeof value === "object") return "days" in value ? "onsite" : "compensation";
  return typeof value;
}
export function validateDefinition(data: SaveDefinition): string | null {
  if (!data.description.trim() || data.description.trim().length > 20000) return "Enter a description of 1–20,000 characters before saving.";
  if (data.preferences.length > 100) return "Keep at most 100 criteria.";
  const keys = new Set<string>();
  for (const p of data.preferences) {
    if (!p.key.trim() || p.key.trim().length > 80 || keys.has(p.key.trim())) return "Give every criterion a unique name of 1–80 characters.";
    keys.add(p.key.trim());
    if ((p.note?.length ?? 0) > 2000) return "Keep criterion notes within 2,000 characters.";
    if (p.value === null) continue;
    if ([...serializedValue(p.value)].length > 4000) return `${label(p.key)}: keep the value within 4,000 characters.`;
    if (p.category === "compensation") {
      if (typeof p.value !== "object" || Array.isArray(p.value) || !("minimum" in p.value)) return "Use a compensation range or Unknown for compensation.";
      const v = p.value;
      if ([v.minimum, v.maximum, v.target].some(n => n !== null && (!Number.isFinite(n) || n < 0))) return "Compensation amounts must be zero or positive.";
      if (v.minimum !== null && v.maximum !== null && v.minimum > v.maximum) return "Minimum compensation cannot exceed maximum compensation.";
      if (v.currency !== null && !/^[A-Z]{3}$/.test(v.currency)) return "Use a three-letter currency code, such as EUR.";
    } else if (typeof p.value === "object" && !Array.isArray(p.value)) {
      if (p.category !== "work_arrangement" || !("days" in p.value)) return "On-site limits belong to work arrangement.";
      if (p.value.days !== null && (!Number.isInteger(p.value.days) || p.value.days < 0 || p.value.days > 366)) return "On-site days must be a whole number from 0 to 366.";
    } else if (typeof p.value === "number" && !Number.isFinite(p.value)) return "Enter a finite number.";
  }
  return null;
}
export function newPreference(existing: Preference[]): Preference {
  let n = existing.length + 1;
  while (existing.some(p => p.key === `criterion_${n}`)) n++;
  return { key: `criterion_${n}`, category: "role", priority: "preferred", value: null, note: null };
}
