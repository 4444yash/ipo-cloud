interface StatsBarProps {
  total: number
  invest: number
  skip: number
}

function StatCard({
  value,
  label,
  accentClass,
}: {
  value: number | string
  label: string
  accentClass: string
}) {
  return (
    <div className="flex-1 rounded-2xl border border-border bg-surface p-5">
      <div className={`text-3xl font-extrabold ${accentClass}`}>{value}</div>
      <div className="mt-1 text-sm text-muted">{label}</div>
    </div>
  )
}

export function StatsBar({ total, invest, skip }: StatsBarProps) {
  return (
    <div className="flex flex-wrap gap-4 px-5 pt-6 md:px-10">
      <StatCard value={total} label="Total IPOs Today" accentClass="text-foreground" />
      <StatCard value={invest} label="INVEST Signals" accentClass="text-invest" />
      <StatCard value={skip} label="SKIP Signals" accentClass="text-skip" />
    </div>
  )
}
