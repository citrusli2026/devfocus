"use client";

import { createContext, use, useCallback, useSyncExternalStore } from "react";
import zhMessages from "../messages/zh.json";
import enMessages from "../messages/en.json";

type Messages = typeof zhMessages;
type Locale = "zh" | "en";

const messages: Record<Locale, Messages> = { zh: zhMessages, en: enMessages };
const STORAGE_KEY = "devfocus-locale";
const DEFAULT_LOCALE: Locale = "zh";

function readLocale(): Locale {
  try {
    const s = window.localStorage.getItem(STORAGE_KEY);
    if (s === "zh" || s === "en") return s;
  } catch {}
  return DEFAULT_LOCALE;
}

function subscribeLocale(callback: () => void): () => void {
  const handler = (e: StorageEvent) => {
    if (e.key === STORAGE_KEY) callback();
  };
  window.addEventListener("storage", handler);
  return () => window.removeEventListener("storage", handler);
}

interface I18nCtx {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: string, params?: Record<string, string | number>) => string;
}

export const I18nContext = createContext<I18nCtx>({
  locale: DEFAULT_LOCALE, setLocale: () => {}, t: (k) => k,
});

function getNested(obj: Record<string, unknown>, path: string): string | undefined {
  const r = path.split(".").reduce<unknown>((a, p) => {
    if (a && typeof a === "object" && !Array.isArray(a)) return (a as Record<string, unknown>)[p];
    return undefined;
  }, obj);
  return typeof r === "string" ? r : undefined;
}

function fmt(tpl: string, params: Record<string, string | number>): string {
  return tpl.replace(/\{(\w+)\}/g, (_, k) => String(params[k] ?? `{${k}}`));
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  // useSyncExternalStore gives a stable server snapshot (DEFAULT_LOCALE) while
  // keeping the locale in sync with localStorage on the client without a flash
  // of mismatched hydration content.
  const locale = useSyncExternalStore<Locale>(
    subscribeLocale,
    readLocale,
    () => DEFAULT_LOCALE
  );

  const setLocale = useCallback((l: Locale) => {
    try { localStorage.setItem(STORAGE_KEY, l); } catch {}
    // Dispatch a storage event so other tabs and the store update immediately
    try {
      window.dispatchEvent(new StorageEvent("storage", { key: STORAGE_KEY, newValue: l }));
    } catch {}
  }, []);

  const t = useCallback((key: string, params?: Record<string, string | number>): string => {
    const v = getNested(messages[locale], key);
    if (v === undefined) return key;
    return params ? fmt(v, params) : v;
  }, [locale]);

  return <I18nContext.Provider value={{ locale, setLocale, t }}>{children}</I18nContext.Provider>;
}

export function useTranslation() {
  const ctx = use(I18nContext);
  if (!ctx) throw new Error("useTranslation must be within I18nProvider");
  return ctx;
}
