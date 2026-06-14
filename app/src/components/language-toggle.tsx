"use client";

import { useTranslation } from "../lib/i18n";

export function LanguageToggle() {
  const { locale, setLocale } = useTranslation();

  return (
    <button
      onClick={() => setLocale(locale === "zh" ? "en" : "zh")}
      className="rounded-lg px-2 py-1 text-xs font-medium text-text-secondary hover:text-text-primary hover:bg-surface-hover transition-colors border border-surface-border cursor-pointer"
      title={locale === "zh" ? "Switch to English" : "切换到中文"}
    >
      {locale === "zh" ? "EN" : "中"}
    </button>
  );
}
