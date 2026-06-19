import type { ReactNode } from "react";

type PageTitleProps = {
  actions?: ReactNode;
  description?: string;
  eyebrow?: string;
  title: string;
};

export function PageTitle({ actions, description, eyebrow, title }: PageTitleProps) {
  return (
    <div className="mb-7 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        {eyebrow && (
          <p className="cv-section-tag px-3 py-1">
            {eyebrow}
          </p>
        )}
        <h1 className="mt-3 text-[1.375rem] font-bold leading-tight text-[var(--text)] sm:text-[1.5rem]">
          {title}
        </h1>
        {description && (
          <p className="mt-2 max-w-xl text-[13px] leading-relaxed text-[var(--text2)]">
            {description}
          </p>
        )}
      </div>
      {actions && (
        <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>
      )}
    </div>
  );
}
