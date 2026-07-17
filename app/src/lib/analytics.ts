import { track } from "@vercel/analytics";

export function trackEvent(
  event: string,
  properties?: Record<string, string | number | boolean | null | undefined>
) {
  try {
    track(event, properties);
  } catch {
    // Analytics may be blocked or unavailable; fail silently
  }
}
