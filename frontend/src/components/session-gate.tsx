"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { ApiError } from "../lib/client";
import { useI18n } from "../lib/i18n/provider";
import { SESSION_EXPIRED } from "../lib/http-transport";
import { MOCK_MODE, sessionApi } from "../lib/runtime-client";

const SessionContext = createContext<{ signOut: () => Promise<void> } | null>(null);
export const useSession = () => useContext(SessionContext);

export function SessionGate({ children }: { children: React.ReactNode }) {
  const { t } = useI18n();
  const [authenticated, setAuthenticated] = useState(false);
  const [opened, setOpened] = useState(false);
  const [busy, setBusy] = useState(!MOCK_MODE);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    if (MOCK_MODE) return;
    let active = true;
    sessionApi.read().then(() => { if (active) { setAuthenticated(true); setOpened(true); } }).catch(e => {
      if (active && (!(e instanceof ApiError) || e.status !== 401)) setError(e.message);
    }).finally(() => { if (active) setBusy(false); });
    const expired = () => { setAuthenticated(false); setError("Your session expired. Sign in again to continue; your edits are still here."); };
    window.addEventListener(SESSION_EXPIRED, expired);
    return () => { active = false; window.removeEventListener(SESSION_EXPIRED, expired); };
  }, []);
  async function login(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try { await sessionApi.login(username, password); setAuthenticated(true); setOpened(true); }
    catch (e) { setError(e instanceof Error ? e.message : "Sign-in failed. Try again."); }
    finally { setPassword(""); setBusy(false); }
  }
  async function signOut() {
    await sessionApi.logout(); setAuthenticated(false); setOpened(false); setError("");
  }
  if (MOCK_MODE) return <main id="main-content" tabIndex={-1}>{children}</main>;
  return <main id="main-content" tabIndex={-1}>
    {!authenticated && <section className="workspace sign-in" aria-labelledby="sign-in-title">
      <p className="eyebrow">{t("Your next chapter")}</p><h1 id="sign-in-title">{t("Sign in to your workspace.")}</h1>
      <p className="lead">{t("Continue clarifying the role you’re looking for. Your saved work stays private.")}</p>
      {busy && <p role="status">{t("Checking access…")}</p>}
      {error && <p role="alert" className="inline-error">{t(error)}</p>}
      <form onSubmit={login} className="card"><fieldset className="workspace-controls" disabled={busy}>
        <legend className="sr-only">{t("Owner sign-in")}</legend>
        <label>{t("Username")}<input autoComplete="username" value={username} maxLength={100} required onChange={e => setUsername(e.target.value)} /></label>
        <label>{t("Password")}<input type="password" autoComplete="current-password" value={password} maxLength={1024} required onChange={e => setPassword(e.target.value)} /></label>
        <button type="submit" className="primary">{t("Sign in")}</button>
      </fieldset></form>
    </section>}
    {opened && <div hidden={!authenticated}><SessionContext.Provider value={{ signOut }}>{children}</SessionContext.Provider></div>}
  </main>;
}
