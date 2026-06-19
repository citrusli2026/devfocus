"use client";

import { useTranslation } from "../lib/i18n";

export function Footer() {
  const { t } = useTranslation();
  return (
    <footer className="border-t border-surface-border mt-12">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-text-muted">
          <div className="flex items-center gap-2">
            <span>⚡</span>
            <span className="font-medium text-text-secondary">{t("nav.brand")}</span>
            <span>—</span>
            <span>{t("nav.brandSub")}</span>
          </div>
          <div className="flex items-center gap-4 flex-wrap justify-center">
            <span>Hacker News</span>
            <span className="text-text-dim">·</span>
            <span>GitHub</span>
            <span className="text-text-dim">·</span>
            <span>Product Hunt</span>
            <span className="text-text-dim">·</span>
            <span>掘金</span>
            <span className="text-text-dim">·</span>
            <span>知乎</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
