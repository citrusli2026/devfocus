"use client";

import { createContext, use, useCallback, useMemo, useSyncExternalStore } from "react";

const STORAGE_KEY = "devfocus-read-items";
const MAX_ITEMS = 500;

interface ReadItemsCtx {
  readIds: Set<string>;
  markAsRead: (id: string) => void;
  markAllAsRead: (ids: string[]) => void;
  isRead: (id: string) => boolean;
}

const ReadItemsContext = createContext<ReadItemsCtx | null>(null);

function readFromStorage(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) return parsed.filter((x) => typeof x === "string");
  } catch {}
  return [];
}

function writeToStorage(ids: string[]) {
  if (typeof window === "undefined") return;
  try {
    const trimmed = ids.slice(-MAX_ITEMS);
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
  } catch {}
}

// Module-level cache and listeners keep snapshots stable across renders and
// avoid hydration mismatches: the server snapshot is always empty.
let cache: Set<string> | null = null;
const listeners = new Set<() => void>();

function getReadIds(): Set<string> {
  if (typeof window === "undefined") return new Set();
  if (!cache) cache = new Set(readFromStorage());
  return cache;
}

function setReadIds(next: Set<string>) {
  cache = next;
  writeToStorage(Array.from(next));
  listeners.forEach((cb) => cb());
}

function subscribeReadIds(callback: () => void): () => void {
  const onStorage = () => {
    cache = new Set(readFromStorage());
    callback();
  };
  window.addEventListener("storage", onStorage);
  listeners.add(callback);
  return () => {
    window.removeEventListener("storage", onStorage);
    listeners.delete(callback);
  };
}

function getServerSnapshot(): Set<string> {
  return new Set();
}

export function ReadItemsProvider({ children }: { children: React.ReactNode }) {
  const readIds = useSyncExternalStore(
    subscribeReadIds,
    getReadIds,
    getServerSnapshot
  );

  const markAsRead = useCallback(
    (id: string) => {
      if (readIds.has(id)) return;
      setReadIds(new Set(readIds).add(id));
    },
    [readIds]
  );

  const markAllAsRead = useCallback(
    (ids: string[]) => {
      const next = new Set(readIds);
      let changed = false;
      for (const id of ids) {
        if (!next.has(id)) {
          next.add(id);
          changed = true;
        }
      }
      if (changed) setReadIds(next);
    },
    [readIds]
  );

  const isRead = useCallback((id: string) => readIds.has(id), [readIds]);

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
