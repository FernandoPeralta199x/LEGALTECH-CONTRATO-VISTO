import { cn } from "@/lib/cn";

type WizardProgressProps = {
  total: number;
  current: number;
  className?: string;
};

export function WizardProgress({ total, current, className }: WizardProgressProps) {
  return (
    <div
      aria-label={`Etapa ${current} de ${total}`}
      aria-valuemax={total}
      aria-valuemin={1}
      aria-valuenow={current}
      className={cn("flex gap-1.5", className)}
      role="progressbar"
    >
      {Array.from({ length: total }).map((_, i) => {
        const idx = i + 1;
        const isActive = idx <= current;
        return (
          <span
            className={cn(
              "h-1 flex-1 rounded-full transition-colors duration-[250ms] ease-smooth",
              isActive ? "bg-[var(--teal)]" : "bg-[var(--surf3)]"
            )}
            key={idx}
          />
        );
      })}
    </div>
  );
}
