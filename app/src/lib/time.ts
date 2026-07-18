const UNITS: { unit: Intl.RelativeTimeFormatUnit; ms: number }[] = [
  { unit: "year", ms: 365 * 24 * 60 * 60 * 1000 },
  { unit: "month", ms: 30 * 24 * 60 * 60 * 1000 },
  { unit: "day", ms: 24 * 60 * 60 * 1000 },
  { unit: "hour", ms: 60 * 60 * 1000 },
  { unit: "minute", ms: 60 * 1000 },
  { unit: "second", ms: 1000 },
];

export function isWithinDays(date: Date | string, days: number): boolean {
  const d = typeof date === "string" ? new Date(date) : date;
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  return diffMs >= 0 && diffMs <= days * 24 * 60 * 60 * 1000;
}

export function formatRelativeTime(
  date: Date | string,
  locale: "zh" | "en" = "zh"
): string {
  const d = typeof date === "string" ? new Date(date) : date;
  const now = new Date();
  const diffMs = d.getTime() - now.getTime();
  const absMs = Math.abs(diffMs);

  const rtf = new Intl.RelativeTimeFormat(locale === "zh" ? "zh-CN" : "en", {
    numeric: "auto",
  });

  for (const { unit, ms } of UNITS) {
    const value = Math.round(absMs / ms);
    if (value >= 1) {
      return rtf.format(diffMs >= 0 ? value : -value, unit);
    }
  }
  return locale === "zh" ? "刚刚" : "just now";
}
