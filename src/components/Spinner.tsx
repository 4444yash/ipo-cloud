interface SpinnerProps {
  label?: string
}

export function Spinner({ label = "Loading…" }: SpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 rounded-2xl border border-border bg-surface p-12 text-muted">
      <div className="h-8 w-8 rounded-full border-2 border-border border-t-accent animate-spin-slow" />
      <span className="text-sm">{label}</span>
    </div>
  )
}
