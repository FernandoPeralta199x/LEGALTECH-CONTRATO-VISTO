"use client";

import { useEffect, useRef, useState } from "react";

import { cn } from "@/lib/cn";

/**
 * CurrencyInput formats values in BRL while the internal state remains cents.
 *
 * - `value` / `defaultValue` are in cents.
 * - `onChange` returns cents.
 * - Empty input emits null (so callers can treat it as "use default").
 */

type CurrencyInputProps = {
  value?: number | null;
  defaultValue?: number | null;
  onChange?: (cents: number | null) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  inputClassName?: string;
  id?: string;
  name?: string;
  "aria-label"?: string;
};

function centsToDisplay(cents: number | null | undefined): string {
  if (cents === null || cents === undefined || Number.isNaN(cents)) return "";
  const reais = Math.round(cents) / 100;
  return reais.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function parseCurrency(value: string): number | null {
  const cleaned = value
    .replace(/[^\d,]/g, "")
    .replace(/\./g, "")
    .replace(",", ".");
  const num = parseFloat(cleaned);
  if (Number.isNaN(num)) return null;
  return Math.round(num * 100);
}

export function CurrencyInput({
  value,
  defaultValue,
  onChange,
  placeholder,
  disabled,
  className,
  inputClassName,
  id,
  name,
  "aria-label": ariaLabel,
}: CurrencyInputProps) {
  const isControlled = value !== undefined;
  const [display, setDisplay] = useState(() =>
    centsToDisplay(isControlled ? value : defaultValue)
  );
  const [focused, setFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isControlled && !focused) {
      setDisplay(centsToDisplay(value));
    }
  }, [isControlled, value, focused]);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const raw = e.target.value;
    const numeric = raw.replace(/[^\d]/g, "");

    // Format as reais,centavos while typing
    let formatted = "";
    if (numeric.length === 0) {
      formatted = "";
    } else if (numeric.length <= 2) {
      formatted = `0,${numeric.padStart(2, "0")}`;
    } else {
      const reais = numeric.slice(0, -2).replace(/^0+/, "") || "0";
      const centavos = numeric.slice(-2);
      formatted = `${parseInt(reais, 10).toLocaleString("pt-BR")},${centavos}`;
    }

    setDisplay(formatted);
    onChange?.(parseCurrency(formatted));
  }

  function handleFocus() {
    setFocused(true);
    if (display === "0,00") {
      setDisplay("");
      onChange?.(null);
    }
  }

  function handleBlur() {
    setFocused(false);
    const cents = parseCurrency(display);
    setDisplay(centsToDisplay(cents));
  }

  return (
    <div
      className={cn(
        "relative inline-flex items-center rounded-lg border border-[var(--bd)] bg-[var(--surf3)] px-3 py-2 text-sm",
        "focus-within:border-[var(--accent)] focus-within:ring-1 focus-within:ring-[var(--accent)]/30",
        disabled && "opacity-60",
        className
      )}
    >
      <span className="pointer-events-none mr-2 text-[var(--text3)]">R$</span>
      <input
        ref={inputRef}
        id={id}
        name={name}
        aria-label={ariaLabel}
        type="text"
        inputMode="decimal"
        disabled={disabled}
        value={display}
        onChange={handleChange}
        onFocus={handleFocus}
        onBlur={handleBlur}
        placeholder={placeholder ?? "0,00"}
        className={cn(
          "w-full border-0 bg-transparent p-0 text-right text-[var(--text)] outline-none placeholder:text-[var(--text3)]",
          inputClassName
        )}
      />
    </div>
  );
}

export function centsToReaisLabel(cents: number | null | undefined): string {
  if (cents === null || cents === undefined || Number.isNaN(cents)) return "R$ —";
  return (Math.round(cents) / 100).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}
