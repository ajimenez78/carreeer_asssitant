// Part 7 HTTP shapes. Keep mock and future HTTP transport behind the same client.
export const categories = ["role", "seniority", "responsibilities", "technical_interests", "company_context", "compensation", "location", "work_arrangement", "work_life_balance"] as const;
export type Category = typeof categories[number];
export type Priority = "mandatory" | "preferred" | "excluded";
export type Compensation = { minimum: number | null; maximum: number | null; target: number | null; currency: string | null; period: "hour" | "day" | "week" | "month" | "year" | null; basis: "gross" | "net" | null };
export type OnsiteLimit = { days: number | null; period: "week" | "month" | "year" | null };
export type PreferenceValue = string | number | boolean | string[] | Compensation | OnsiteLimit | null;
export type Preference = { key: string; category: Category; priority: Priority; value: PreferenceValue; note: string | null };
export type SaveDefinition = { description: string; state: "draft" | "ready"; preferences: Preference[]; proposal_context?: string };
export type SourceMetadata = {
  id: string; kind: "file" | "url" | "text"; display_name: string; url: string | null;
  media_type: string | null; size_bytes: number | null; extraction_state: "pending" | "ready" | "failed";
  extraction_error: { code: string; message: string } | null; original_stored: boolean;
  reviewed_at: string | null; created_at: string;
};
export type SourceView = SourceMetadata & { extracted_text: string | null; facts: { id: string; source_id: string; content: string }[] };
export type AnswerState = "answered" | "skipped" | "unknown";
export type Question = { id: string; round_id: string; position: number; question: string; answer_state: AnswerState | "unanswered"; answer: string | null };
export type Definition = Omit<SaveDefinition, "proposal_context"> & { id: string; created_at: string; updated_at: string; sources: SourceMetadata[]; clarifications: Question[] };
export type Usage = { model: string; input_tokens: number; output_tokens: number; estimated_cost_usd: string | null };
export type ClarificationProposal = { proposal: { preferences: Preference[]; conflicts: string[] }; clarifications: Question[]; proposal_context: string; usage: Usage };
export type BackgroundProposal = { source_id: string; proposal: { facts: { content: string; evidence: string }[]; unknowns: string[] }; usage: Usage };
export type SourceInput = { kind: "text"; display_name: string; text: string } | { kind: "url"; display_name: string; url: string };
export type Cleanup = { cleanup_pending: boolean; pending_originals: number };
export type Language = "English" | "Spanish";
