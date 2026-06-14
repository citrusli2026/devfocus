import { ReactNode } from "react";

export function SectionHeader({
  icon,
  title,
  count,
  color = "text-accent-violet",
}: {
  icon: string;
  title: string;
  count?: number;
  color?: string;
}) {
  return (
    <div className="flex items-center gap-2.5 mb-5">
      <span className={`text-xl ${color}`}>{icon}</span>
      <h2 className="text-xl font-bold text-text-primary">{title}</h2>
      {count !== undefined && (
        <span className="text-sm font-medium text-text-dim bg-surface-hover px-2 py-0.5 rounded-md tabular-nums">
          {count}
        </span>
      )}
    </div>
  );
}

export function Badge({ children, variant = "default" }: { children: ReactNode; variant?: "default" | "violet" | "lime" }) {
  const variants = {
    default: "bg-surface-hover text-text-muted",
    violet: "bg-accent-violet/10 text-accent-violet",
    lime: "bg-accent-lime/10 text-accent-lime",
  };
  return (
    <span className={`inline-flex items-center text-xs font-medium px-2.5 py-1 rounded-lg ${variants[variant]}`}>
      {children}
    </span>
  );
}
