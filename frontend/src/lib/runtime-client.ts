import { createClient, requestApi, type Transport } from "./client";
import { createHttpTransport } from "./http-transport";

export const MOCK_MODE = process.env.NEXT_PUBLIC_API_MODE === "mock";
const http = createHttpTransport();
const transport: Transport = async (path, init) => {
  if (MOCK_MODE) {
    const { createMockTransport } = await import("./mock-transport");
    return createMockTransport(window.localStorage, window.sessionStorage)(path, init);
  }
  return http(path, init);
};
export const api = createClient(transport);
export const sessionApi = {
  read: () => requestApi(http, "/session"),
  login: (username: string, password: string) => requestApi(http, "/session", "POST", { username, password }),
  logout: () => requestApi<void>(http, "/session", "DELETE"),
};
