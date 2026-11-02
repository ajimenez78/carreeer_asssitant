import { API_BASE_URL } from "./api-config";
import type { Transport } from "./client";

export const SESSION_EXPIRED = "career:session-expired";
export function createHttpTransport(baseURL = API_BASE_URL, fetcher: typeof fetch = fetch): Transport {
  return async (path, init) => {
    const response = await fetcher(`${baseURL}${path}`, { ...init, credentials: "include", cache: "no-store" });
    if (response.status === 401 && path !== "/session" && typeof window !== "undefined") window.dispatchEvent(new Event(SESSION_EXPIRED));
    return response;
  };
}
