"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { isLocale, LOCALE_STORAGE_KEY, translate, type Locale } from "./catalogs";

type I18n = { locale: Locale; setLocale: (locale: Locale) => void; t: (message: string, values?: Record<string, string | number>) => string };
const Context = createContext<I18n>({ locale: "en", setLocale: () => {}, t: (message, values) => translate("en", message, values) });

export function I18nProvider({ children }: { children: React.ReactNode }) {
  // Start in English on both server and client to keep the static export hydratable.
  const [locale, updateLocale] = useState<Locale>("en");
  useEffect(() => {
    try { const stored = localStorage.getItem(LOCALE_STORAGE_KEY); if (isLocale(stored)) updateLocale(stored); } catch { /* Switching still works without browser storage. */ }
  }, []);
  useEffect(() => {
    document.documentElement.lang = locale;
    document.title = translate(locale, "The role you’re looking for | Career assistant");
    document.querySelector('meta[name="description"]')?.setAttribute("content", translate(locale, "Clarify what you’re looking for in a role, from responsibilities to work–life balance."));
  }, [locale]);
  function setLocale(next: Locale) {
    updateLocale(next);
    try { localStorage.setItem(LOCALE_STORAGE_KEY, next); } catch { /* Do not block editing when persistence is unavailable. */ }
  }
  return <Context.Provider value={{ locale, setLocale, t: (message, values) => translate(locale, message, values) }}>{children}</Context.Provider>;
}
export const useI18n = () => useContext(Context);
