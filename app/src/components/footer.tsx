"use client";

import Link from "next/link";
import { useTranslation } from "../lib/i18n";
import { getSourceMeta } from "../lib/sources";
import { GitHubIcon } from "./icons";
import digestData from "../data/digest.json";
import type { Digest } from "../types";

export function Footer() {
  const { t } = useTranslation();
  const digest = digestData as Digest;
  const sources = digest.sources ?? [];

  const links = [
    { href: "/", label: t("nav.today") },
    { href: "/history/", label: t("history.title") },
    { href: "/search/", label: t("nav.search") },
    { href: "/weekly/", label: t("nav.weekly") },
    { href: "/about/", label: t("nav.about") },
  ];

  return (
    <footer className="border-t border-surface-border mt-12">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <div className="flex flex-col items-center gap-6">
          {/* Nav links */}
          <nav className="flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-sm font-medium">
            {links.map(({ href, label }) => (
              <Link
                key={href}
                href={href}
                className="text-text-secondary hover:text-text-primary transition-colors"
              >
                {label}
              </Link>
            ))}
          </nav>

          {/* Source badges */}
          <div className="flex items-center gap-3 flex-wrap justify-center">
            {sources.map((src) => {
              const meta = getSourceMeta(src);
              return (
                <span
                  key={src}
                  className={`inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium border ${meta.bg} ${meta.color} border-current/10`}
                >
                  {meta.icon}
                  {meta.shortLabel}
                </span>
              );
            })}
          </div>

          {/* Bottom row */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 w-full text-sm text-text-muted border-t border-surface-border pt-6">
            <div className="flex items-center gap-2">
              <span>⚡</span>
              <span className="font-medium text-text-secondary">{t("nav.brand")}</span>
              <span>—</span>
              <span>{t("nav.brandSub")}</span>
            </div>
            <div className="flex items-center gap-4">
              <a
                href="https://github.com/citrusli2026/devfocus"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-text-secondary hover:text-text-primary transition-colors"
              >
                <GitHubIcon className="h-4 w-4" />
                GitHub
              </a>
              <a
                href="/feed.xml"
                className="text-text-secondary hover:text-text-primary transition-colors"
              >
                RSS
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
