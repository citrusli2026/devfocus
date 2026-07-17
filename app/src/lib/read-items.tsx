"use client";

import { createContext, use, useCallback, useLayoutEffect, useMemo, useState } from "react";

const STORAGE_KEY = "devfocus-read-items";
const MAX_ITEMS = 500;

interface ReadItemsCtx {
  readIds: Set<string>;
  markAsRead: (id: string) => void;
  markAllAsRead: (ids: string[]) => void;
  isRead: (id: string) => boolean;
}

const ReadItemsContext = createContext<ReadItemsCtx | null>(null);

function loadIds(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) return parsed.filter((x) => typeof x === "string");
  } catch {}
  return [];
}

function saveIds(ids: string[]) {
  if (typeof window === "undefined") return;
  try {
    const trimmed = ids.slice(-MAX_ITEMS);
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
  } catch {}
}

export function ReadItemsProvider({ children }: { children: React.ReactNode }) {
  const [readIds, setReadIds] = useState<Set<string>>(() => new Set(loadIds()));

  useLayoutEffect(() => {
    const handler = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY) {
        setReadIds(new Set(loadIds()));
      }
    };
    window.addEventListener("storage", handler);
    return () => window.removeEventListener("storage", handler);
  }, []);

  useLayoutEffect(() => {
    saveIds(Array.from(readIds));
  }, [readIds]);

  const markAsRead = useCallback((id: string) => {
    setReadIds((prev) => {
      if (prev.has(id)) return prev;
      return new Set(prev).add(id);
    });
  }, []);

  const markAllAsRead = useCallback((ids: string[]) => {
    setReadIds((prev) => {
      const next = new Set(prev);
      ids.forEach((id) => next.add(id));
      return next;
    });
  }, []);

  const isRead = useCallback(
    (id: string) => readIds.has(id),
    [readIds]
  );

  const value = useMemo(
    () => ({ readIds, markAsRead, markAllAsRead, isRead }),
    [readIds, markAsRead, markAllAsRead, isRead]
  );

  return (
    <ReadItemsContext.Provider value={value}>
      {children}
    </ReadItemsContext.Provider>
  );
}

export function useReadItems() {
  const ctx = use(ReadItemsContext);
  if (!ctx) throw new Error("useReadItems must be within ReadItemsProvider");
  return ctx;
}
