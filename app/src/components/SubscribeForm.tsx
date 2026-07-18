"use client";

import { useState } from "react";
import { Mail, Check, AlertCircle } from "lucide-react";
import { useTranslation } from "../lib/i18n";
import { trackEvent } from "../lib/analytics";

const SUBSCRIBE_URL = process.env.NEXT_PUBLIC_SUBSCRIBE_URL;

export function SubscribeForm() {
  const { t } = useTranslation();
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.includes("@")) {
      setStatus("error");
      setMessage(t("subscribe.invalidEmail"));
      return;
    }

    trackEvent("subscribe_intent", { has_backend: !!SUBSCRIBE_URL });

    if (SUBSCRIBE_URL) {
      try {
        const formData = new FormData();
        formData.append("email", email);
        await fetch(SUBSCRIBE_URL, {
          method: "POST",
          body: formData,
          mode: "no-cors",
        });
        setStatus("success");
        setMessage(t("subscribe.success"));
        setEmail("");
      } catch {
        setStatus("error");
        setMessage(t("subscribe.error"));
      }
    } else {
      // No backend configured yet — record intent locally and be honest about it
      try {
        const list = JSON.parse(localStorage.getItem("devfocus-subscribe-intent") || "[]");
        list.push({ email, date: new Date().toISOString() });
        localStorage.setItem("devfocus-subscribe-intent", JSON.stringify(list.slice(-100)));
      } catch {}
      setStatus("success");
      setMessage(t("subscribe.comingSoon"));
      setEmail("");
    }
  };

  return (
    <section className="rounded-2xl bg-surface-card border border-surface-border p-6 sm:p-8">
      <div className="flex flex-col sm:flex-row sm:items-center gap-4 sm:gap-8">
        <div className="flex-1">
          <h2 className="text-lg font-bold text-text-primary flex items-center gap-2">
            <Mail className="h-5 w-5 text-accent-violet" />
            {t("subscribe.title")}
          </h2>
          <p className="mt-1 text-sm text-text-secondary">{t("subscribe.desc")}</p>
        </div>

        <form onSubmit={handleSubmit} className="flex-1 max-w-md">
          <div className="flex gap-2">
            <input
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                if (status !== "idle") setStatus("idle");
              }}
              placeholder={t("subscribe.placeholder")}
              className="flex-1 px-4 py-2.5 rounded-lg bg-surface-hover border border-surface-border text-text-primary placeholder:text-text-dim focus:outline-none focus:border-accent-violet/50 text-sm"
              required
            />
            <button
              type="submit"
              className="px-4 py-2.5 rounded-lg bg-accent-violet text-white text-sm font-semibold hover:bg-accent-violet/90 transition-colors"
            >
              {t("subscribe.button")}
            </button>
          </div>
          {status !== "idle" && (
            <div className={`mt-2 text-xs flex items-center gap-1 ${status === "success" ? "text-accent-emerald" : "text-red-500"}`}>
              {status === "success" ? <Check className="h-3.5 w-3.5" /> : <AlertCircle className="h-3.5 w-3.5" />}
              {message}
            </div>
          )}
        </form>
      </div>
    </section>
  );
}
