import type {
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes
} from "react";

import { cn } from "@/lib/cn";

type FormFieldProps = {
  children: ReactNode;
  error?: string;
  hint?: string;
  htmlFor?: string;
  label: string;
  required?: boolean;
};

const controlBase =
  "cv-input w-full disabled:cursor-not-allowed disabled:opacity-55";

function controlClass(invalid?: boolean, className?: string): string {
  return cn(
    controlBase,
    invalid
      ? "cv-input-invalid"
      : "",
    className
  );
}

export function FormField({
  children,
  error,
  hint,
  htmlFor,
  label,
  required = false
}: FormFieldProps) {
  return (
    <label className="block" htmlFor={htmlFor}>
      <span className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold text-[var(--text2)]">
        {label}
        {required && <span className="text-red-500">*</span>}
      </span>
      {children}
      {error ? (
        <p className="mt-1.5 text-xs leading-5 text-red-700 dark:text-red-300">{error}</p>
      ) : hint ? (
        <p className="mt-1.5 text-xs leading-5 text-[var(--text2)]">{hint}</p>
      ) : null}
    </label>
  );
}

type TextInputProps = InputHTMLAttributes<HTMLInputElement> & {
  invalid?: boolean;
};

export function TextInput({ className, invalid, ...props }: TextInputProps) {
  return (
    <input
      aria-invalid={invalid || undefined}
      className={controlClass(invalid, cn("px-3", className))}
      {...props}
    />
  );
}

type TextAreaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  invalid?: boolean;
};

export function TextArea({ className, invalid, ...props }: TextAreaProps) {
  return (
    <textarea
      aria-invalid={invalid || undefined}
      className={controlClass(invalid, cn("min-h-24 resize-y px-3 py-2", className))}
      {...props}
    />
  );
}

type SelectInputProps = SelectHTMLAttributes<HTMLSelectElement> & {
  invalid?: boolean;
};

export function SelectInput({ className, invalid, ...props }: SelectInputProps) {
  return (
    <select
      aria-invalid={invalid || undefined}
      className={controlClass(
        invalid,
        cn(
          "px-3 [color-scheme:inherit] [&_option]:bg-[var(--surf)] [&_option]:text-[var(--text)] [&_option:checked]:bg-[var(--surf2)]",
          className
        )
      )}
      {...props}
    />
  );
}
