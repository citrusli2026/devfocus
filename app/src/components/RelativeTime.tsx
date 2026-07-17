"use client";

import { useSyncExternalStore } from "react";
import { formatRelativeTime } from "../lib/time";

const subscribe = () => () => {};
const getClientSnapshot = () => true;
const getServerSnapshot = () => false;

export function RelativeTime({
  date,
  locale,
  fallback,
}: {
  date: Date | string;
  locale: "zh" | "en";
  fallback?: string;
}) {
  const isClient = useSyncExternalStore(subscribe, getClientSnapshot, getServerSnapshot);
  if (!isClient) return <span suppressHydrationWarning>{fallback}</span>;
  return <span suppressHydrationWarning>{formatRelativeTime(date, locale)}</span>;
}
