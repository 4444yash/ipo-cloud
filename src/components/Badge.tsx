import type { ReactNode } from "react"

type Variant = "invest" | "skip" | "mainboard" | "sme" | "neutral"

const VARIANT_CLASSES: Record<Variant, string> = {
  invest: "bg-invest/12 text-invest border-invest/30",
  skip: "bg-skip/10 text-skip border-skip/30",
  mainboard: "bg-accent/12 text-accent border-accent/30",
  sme: "bg-gold/12 text-gold border-gold/30",
  neutral: "bg-white/5 text-muted border-border",
}

interface BadgeProps {
  variant: Variant
  children: ReactNode
  className?: string
}

export function Badge({ variant, children, className = "" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-semibold leading-none ${VARIANT_CLASSES[variant]} ${className}`}
    >
      {children}
    </span>
  )
}
