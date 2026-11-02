import { expect, test } from "@playwright/test";
import { createClient, requestApi } from "../../src/lib/client";
import { createHttpTransport } from "../../src/lib/http-transport";

test("HTTP transport uses the configured API, cookies, no-store and multipart boundaries", async () => {
  const calls: { url: string; init: RequestInit }[] = [];
  const transport = createHttpTransport("https://api.example/api", async (input, init) => {
    calls.push({ url: String(input), init: init! }); return Response.json({ id: "synthetic" });
  });
  const api = createClient(transport);
  await api.read(); await api.addSource(new File(["CV"], "cv.md"));
  expect(calls[0].url).toBe("https://api.example/api/job-definition");
  expect(calls[0].init).toMatchObject({ credentials: "include", cache: "no-store" });
  expect(calls[1].init.body).toBeInstanceOf(FormData);
  expect(calls[1].init.headers).toBeUndefined();
});

test("session logout accepts an empty 204 response", async () => {
  await expect(requestApi(async () => new Response(null, { status: 204 }), "/session", "DELETE")).resolves.toBeUndefined();
});

test("proxy HTML and malformed API errors become recoverable sanitized errors", async () => {
  for (const response of [new Response("<html>private proxy diagnostic</html>", { status: 502 }), Response.json({ internal: "diagnostic" }, { status: 503 })]) {
    await expect(createClient(async () => response).read()).rejects.toMatchObject({ code: "unexpected_response", message: "The service returned an unexpected response. Your input is still here. Try again." });
  }
});
