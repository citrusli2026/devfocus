"use client";

import Link from "next/link";
import { Home, History, SearchX } from "lucide-react";
import { useTranslation } from "@/lib/i18n";

export default function NotFound() {
  const { t } = useTranslation();

  return (
    <div className="max-w-2xl mx-auto py-16 sm:py-24 text-center">
      <div className="inline-flex items-center justify-center h-20 w-20 rounded-3xl bg-surface-hover text-text-dim mb-6">
        <SearchX className="h-10 w-10" />
      </div>
      <h1 className="text-4xl sm:text-5xl font-bold text-text-primary mb-3">
        404
      </h1>
      <p className="text-lg sm:text-xl text-text-secondary mb-2">
        {t("notFound.title")}
      </p>
      <p className="text-sm text-text-muted mb-8">
        {t("notFound.subtitle")}
      </p>
      <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-accent-violet text-white font-semibold hover:bg-accent-violet/90 transition-colors"
        >
          <Home className="h-4 w-4" />
          {t("notFound.backHome")}
        </Link>
        <Link
          href="/history/"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-surface-hover text-text-secondary font-semibold hover:bg-surface-elevated transition-colors"
        >
          <History className="h-4 w-4" />
          {t("notFound.viewHistory")}
        </Link>
      </div>
    </div>
  );
}
