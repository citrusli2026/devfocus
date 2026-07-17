"use client";

import { SearchX, Inbox, FileX } from "lucide-react";
import { ReactNode } from "react";

const icons = {
  search: SearchX,
  inbox: Inbox,
  file: FileX,
};

export function EmptyState({
  title,
  hint,
  icon = "inbox",
  children,
}: {
  title: string;
  hint?: string;
  icon?: keyof typeof icons;
  children?: ReactNode;
}) {
  const Icon = icons[icon];
  return (
    <div className="text-center py-14 sm:py-20 px-4">
      <div className="inline-flex items-center justify-center h-12 w-12 rounded-2xl bg-surface-hover text-text-dim mb-4">
        <Icon className="h-6 w-6" />
      </div>
      <p className="text-lg font-semibold text-text-primary">{title}</p>
      {hint && <p className="text-sm text-text-muted mt-1">{hint}</p>}
      {children && <div className="mt-4">{children}</div>}
    </div>
  );
}
