"use client";

import { useEffect, useRef } from "react";
import { useI18n } from "../lib/i18n/provider";

// Shared assistant surface, independent of the current workflow's navigation.
export function AssistantDock({ open, onOpenChange, children }: {
  open: boolean; onOpenChange: (open: boolean) => void; children: React.ReactNode;
}) {
  const { t } = useI18n();
  const launcher = useRef<HTMLButtonElement>(null);
  const panel = useRef<HTMLElement>(null);
  useEffect(() => {
    if (!open) return;
    panel.current?.querySelector<HTMLTextAreaElement>("textarea")?.focus({ preventScroll: true });
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape" && panel.current?.contains(event.target as Node)) {
        event.preventDefault(); onOpenChange(false); launcher.current?.focus();
      }
    };
    document.addEventListener("keydown", escape);
    return () => document.removeEventListener("keydown", escape);
  }, [open, onOpenChange]);

  function minimize() { onOpenChange(false); launcher.current?.focus(); }
  return <div className="assistant-dock">
    <aside id="career-assistant-panel" ref={panel} className="assistant-panel" aria-label={t("Career assistant chat")} hidden={!open}>
      <header className="assistant-panel-heading"><div><strong>{t("Career assistant")}</strong><p>{t("Here throughout your career journey.")}</p></div>
        <button type="button" onClick={minimize} aria-label={t("Minimize assistant")}>−</button>
      </header>
      <div className="assistant-panel-content">{children}</div>
    </aside>
    <button type="button" className="primary assistant-launcher" ref={launcher} aria-expanded={open} aria-controls="career-assistant-panel" onClick={() => open ? minimize() : onOpenChange(true)}>
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="M5 4h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H9l-6 3V6a2 2 0 0 1 2-2Z" /></svg>
      {t("Chat with assistant")}
    </button>
  </div>;
}
