"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "../lib/utils";
import { Newspaper, Info, Search, Trophy, Menu, X, Zap } from "lucide-react";
import { LanguageToggle } from "./language-toggle";
import { ThemeToggle } from "./theme-toggle";
import { GitHubIcon } from "./icons";
import { useTranslation } from "../lib/i18n";
import { useState } from "react";

const navItems = [
  { href: "/", labelKey: "nav.today", icon: Newspaper },
  { href: "/search/", labelKey: "nav.search", icon: Search },
  { href: "/weekly/", labelKey: "nav.weekly", icon: Trophy },
  { href: "/about/", labelKey: "nav.about", icon: Info },
];

export function Navbar() {
  const pathname = usePathname();
  const { t } = useTranslation();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 w-full backdrop-blur-xl navbar-glass">
      <div className="mx-auto flex h-14 sm:h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-accent-violet to-accent-coral shadow-sm">
            <Zap className="h-[18px] w-[18px] text-white" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-lg sm:text-xl font-bold bg-gradient-to-r from-text-primary to-text-secondary bg-clip-text text-transparent">
              {t("nav.brand")}
            </span>
            <span className="text-xs text-text-dim hidden sm:inline font-medium">
              {t("nav.brandSub")}
            </span>
          </div>
        </Link>

        <div className="hidden sm:flex items-center gap-2">
          <nav className="flex items-center gap-1">
            {navItems.map(({ href, labelKey, icon: Icon }) => {
              const active = pathname === href;
              return (
                <Link
                  key={href}
                  href={href}
                  className={cn(
                    "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200",
                    active
                      ? "bg-surface-hover text-text-primary shadow-sm"
                      : "text-text-secondary hover:bg-surface-card hover:text-text-primary"
                  )}
                  aria-current={active ? "page" : undefined}
                >
                  <Icon className="h-4 w-4" />
                  <span>{t(labelKey)}</span>
                </Link>
              );
            })}
          </nav>
          <div className="w-px h-6 bg-surface-border mx-1" />
          <LanguageToggle />
          <ThemeToggle />
          <a
            href="https://github.com/citrusli2026/devfocus"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center h-9 w-9 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-card transition-colors"
            title="GitHub"
          >
            <GitHubIcon className="h-5 w-5" />
          </a>
        </div>

        <div className="flex sm:hidden items-center gap-1">
          <LanguageToggle />
          <ThemeToggle />
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="flex items-center justify-center h-9 w-9 rounded-lg text-text-secondary hover:bg-surface-card transition-colors"
            aria-label={mobileOpen ? t("nav.closeMenu") : t("nav.openMenu")}
            aria-expanded={mobileOpen}
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="sm:hidden border-t border-surface-border bg-surface-elevated">
          <nav className="flex flex-col px-4 py-3 gap-1">
            {navItems.map(({ href, labelKey, icon: Icon }) => {
              const active = pathname === href;
              return (
                <Link
                  key={href}
                  href={href}
                  onClick={() => setMobileOpen(false)}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium transition-all",
                    active ? "bg-surface-hover text-text-primary" : "text-text-secondary hover:bg-surface-card"
                  )}
                  aria-current={active ? "page" : undefined}
                >
                  <Icon className="h-4 w-4" />
                  <span>{t(labelKey)}</span>
                </Link>
              );
            })}
            <div className="my-1 border-t border-surface-border" />
            <a
              href="https://github.com/citrusli2026/devfocus"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium text-text-secondary hover:bg-surface-card hover:text-text-primary transition-all"
            >
              <GitHubIcon className="h-4 w-4" />
              <span>GitHub</span>
            </a>
          </nav>
        </div>
      )}
    </header>
  );
}
