"use client";

import { Moon, Sun, Monitor } from "lucide-react";
import { useTheme } from "./theme-provider";
import { trackEvent } from "../lib/analytics";
import { cn } from "../lib/utils";

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, setTheme } = useTheme();

  return (
    <div className={cn("flex items-center rounded-lg bg-surface-hover p-0.5 border border-surface-border", className)}>
      {(["light", "system", "dark"] as const).map((t) => {
        const Icon = t === "light" ? Sun : t === "dark" ? Moon : Monitor;
        const active = theme === t;
        return (
          <button
            key={t}
            onClick={() => {
              setTheme(t);
              trackEvent("theme_change", { theme: t });
            }}
            className={cn(
              "flex items-center justify-center h-7 w-7 rounded-md text-sm transition-colors",
              active
                ? "bg-surface-card text-text-primary shadow-sm"
                : "text-text-dim hover:text-text-secondary"
            )}
            aria-label={t === "light" ? "Light mode" : t === "dark" ? "Dark mode" : "System theme"}
            title={t === "light" ? "Light" : t === "dark" ? "Dark" : "System"}
          >
            <Icon className="h-3.5 w-3.5" />
          </button>
        );
      })}
    </div>
  );
}
