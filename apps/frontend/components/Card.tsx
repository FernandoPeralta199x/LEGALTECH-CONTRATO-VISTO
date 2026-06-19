import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

type CardProps = {
  actions?: ReactNode;
  children?: ReactNode;
  className?: string;
  description?: string;
  /** Adds a blue glow shadow */
  glow?: boolean;
  /** Enables hover lift + border brightening */
  interactive?: boolean;
  title?: string;
};

export function Card({
  actions,
  children,
  className,
  description,
  glow,
  interactive,
  title
}: CardProps) {
  return (
    <section
      className={cn(
        "cv-card p-5",
        glow && "shadow-glow",
        interactive && "cv-card-hover cursor-pointer",
        className
      )}
    >
      {(title || description || actions) && (
        <div className="mb-5 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <div>
            {title && (
              <h2 className="text-sm font-semibold leading-snug text-[var(--text)]">
                {title}
              </h2>
            )}
            {description && (
              <p className="mt-0.5 text-xs leading-5 text-[var(--text2)]">{description}</p>
            )}
          </div>
          {actions && (
            <div className="flex shrink-0 items-center gap-2">{actions}</div>
          )}
        </div>
      )}
      {children}
    </section>
  );
}
