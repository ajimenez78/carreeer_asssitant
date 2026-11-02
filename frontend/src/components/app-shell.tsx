"use client";

import Link from "next/link";
import { locales, type Locale } from "../lib/i18n/catalogs";
import { useI18n } from "../lib/i18n/provider";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { t, locale, setLocale } = useI18n();
  return <>
    <a className="skip-link" href="#main-content">{t("Skip to content")}</a>
    <header className="site-header"><div className="header-inner">
      <Link className="brand" href="/">{t("Career assistant")}</Link>
      <div className="header-actions">
        <nav aria-label={t("Main navigation")}><Link className="nav-link" href="/" aria-current="page">{t("Your target role")}</Link></nav>
        <label className="locale-switcher">{t("Interface language")}
          <select value={locale} onChange={e => setLocale(e.target.value as Locale)}>{Object.entries(locales).map(([key, language]) => <option key={key} value={key} lang={key}>{language.name}</option>)}</select>
        </label>
      </div>
    </div></header>
    {children}
    <footer className="site-footer">{t("A clearer direction for your next role.")}</footer>
  </>;
}
