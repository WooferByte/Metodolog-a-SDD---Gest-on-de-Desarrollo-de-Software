/**
 * Input — accessible form input with label and error support.
 *
 * Props:
 *   id       — links <label> and <input> via htmlFor / id
 *   label    — visible label text
 *   error    — error message string; sets aria-invalid + role="alert"
 *   type     — input type (text, email, password, etc.)
 *   className — merged via cn() onto <input>
 *
 * WCAG AA: label association, aria-invalid, aria-describedby, role="alert".
 */

import type { InputHTMLAttributes } from 'react'
import { cn } from '@/shared/lib/utils'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

export function Input({ label, error, id, className, ...props }: InputProps) {
  const inputId = id ?? `input-${label?.toLowerCase().replace(/\s+/g, '-')}`
  const errorId = `${inputId}-error`

  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label
          htmlFor={inputId}
          className="text-sm font-medium text-foreground"
        >
          {label}
        </label>
      )}
      <input
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        className={cn(
          'flex h-10 w-full rounded-lg border border-border',
          'bg-background px-3 py-2 text-sm text-foreground',
          'placeholder:text-muted-foreground',
          'focus-visible:outline-none focus-visible:ring-2',
          'focus-visible:ring-ring focus-visible:ring-offset-2',
          'disabled:cursor-not-allowed disabled:opacity-50',
          'transition-colors duration-150',
          error && 'border-destructive focus-visible:ring-destructive',
          className,
        )}
        {...props}
      />
      {error && (
        <p
          id={errorId}
          role="alert"
          className="text-sm text-destructive"
        >
          {error}
        </p>
      )}
    </div>
  )
}
