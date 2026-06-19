import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

export type BadgeTone = "teal" | "orange" | "blue" | "muted";

type BadgeProps = {
  children: ReactNode;
  tone?: BadgeTone;
  className?: string;
};

const toneClass: Record<BadgeTone, string> = {
  teal: "cv-badge-teal",
  orange: "cv-badge-orange",
  blue: "cv-badge-blue",
  muted: "cv-badge-muted"
};

export function Badge({ children, tone = "muted", className }: BadgeProps) {
  return <span className={cn("cv-badge", toneClass[tone], className)}>{children}</span>;
}
