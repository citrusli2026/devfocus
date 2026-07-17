"use client";

import { useTranslation } from "../lib/i18n";
import { getSourceMeta } from "../lib/sources";
import digestData from "../data/digest.json";
import type { Digest } from "../types";

export function Footer() {
  const { t } = useTranslation();
  const digest = digestData as Digest;
  const sources = digest.sources ?? [];

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
            {sources.map((src, idx) => {
              const meta = getSourceMeta(src);
              return (
                <span key={src} className="flex items-center gap-4">
                  <span>{meta.shortLabel}</span>
                  {idx < sources.length - 1 && <span className="text-text-dim">·</span>}
                </span>
              );
            })}
          </div>
        </div>
      </div>
    </footer>
  );
}
