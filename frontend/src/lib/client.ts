import type { AnswerState, BackgroundProposal, ClarificationProposal, Cleanup, Definition, Language, Question, SaveDefinition, SourceInput, SourceView } from "./contracts";

export type Transport = (path: string, init: RequestInit) => Promise<Response>;
export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string, public fields: Record<string, unknown> = {}) { super(message); }
}

export function createClient(transport: Transport) {
  async function request<T>(path: string, method = "GET", body?: unknown): Promise<T> {
    const multipart = body instanceof FormData;
    let response: Response;
    try {
      response = await transport(`/job-definition${path}`, {
        method, credentials: "include",
        headers: body && !multipart ? { "Content-Type": "application/json" } : undefined,
        body: body === undefined ? undefined : multipart ? body : JSON.stringify(body),
      });
    } catch {
      throw new ApiError(0, "network", "Could not reach the service. Your input is still here. Try again.");
    }
    const result = await response.json();
    if (!response.ok) throw new ApiError(response.status, result.error.code, result.error.message, result.error.fields);
    return result as T;
  }
  return {
    read: () => request<Definition>(""),
    save: (data: SaveDefinition) => request<Definition>("", "PUT", data),
    remove: () => request<Cleanup>("", "DELETE"),
    cleanup: () => request<Cleanup>("/cleanup", "POST"),
    addSource: (data: SourceInput | File) => {
      if (data instanceof File) { const form = new FormData(); form.set("file", data); return request<SourceView>("/sources", "POST", form); }
      return request<SourceView>("/sources", "POST", data);
    },
    source: (id: string) => request<SourceView>(`/sources/${id}`),
    reviewSource: (id: string, facts: string[]) => request<SourceView>(`/sources/${id}`, "PATCH", { facts }),
    retrySource: (id: string) => request<SourceView>(`/sources/${id}/retry`, "POST"),
    removeSource: (id: string) => request<Cleanup>(`/sources/${id}`, "DELETE"),
    suggestFacts: (id: string, language: Language) => request<BackgroundProposal>(`/sources/${id}/facts`, "POST", { language }),
    clarify: (language: Language) => request<ClarificationProposal>("/clarifications", "POST", { language }),
    answer: (id: string, state: AnswerState, answer?: string) => request<Question>(`/clarifications/${id}`, "PATCH", state === "answered" ? { state, answer } : { state }),
  };
}
export type Client = ReturnType<typeof createClient>;
