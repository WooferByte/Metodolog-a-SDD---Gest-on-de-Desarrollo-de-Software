/**
 * Card — compound component for content containers.
 *
 * Usage:
 * ```tsx
 * <Card>
 *   <CardHeader>
 *     <CardTitle>Title</CardTitle>
 *   </CardHeader>
 *   <CardContent>Content here</CardContent>
 *   <CardFooter>
 *     <Button>Save</Button>
 *   </CardFooter>
 * </Card>
 * ```
 *
 * All sub-components accept className for style overrides via cn().
 * Uses semantic tokens: bg-card, text-card-foreground, border-border.
 */

import type { HTMLAttributes } from 'react'
import { cn } from '@/shared/lib/utils'

// ── Card root ──────────────────────────────────────────────────

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'rounded-xl border border-border bg-card text-card-foreground shadow-sm',
        className,
      )}
      {...props}
    />
  )
}

// ── Card header ────────────────────────────────────────────────

export function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('flex flex-col space-y-1.5 p-6', className)}
      {...props}
    />
  )
}

// ── Card title ─────────────────────────────────────────────────

export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn('text-xl font-semibold leading-none tracking-tight', className)}
      {...props}
    />
  )
}

// ── Card description ───────────────────────────────────────────

export function CardDescription({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn('text-sm text-muted-foreground', className)}
      {...props}
    />
  )
}

// ── Card content ───────────────────────────────────────────────

export function CardContent({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('p-6 pt-0', className)}
      {...props}
    />
  )
}

// ── Card footer ────────────────────────────────────────────────

export function CardFooter({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('flex items-center p-6 pt-0', className)}
      {...props}
    />
  )
}
