import type { MarketMeter as MarketMeterData } from "../types"

const ARC_PATH = "M 16 90 A 74 74 0 0 1 164 90"
const ARC_LENGTH = Math.PI * 74 // semicircle length for r=74

interface MarketMeterProps {
  data: MarketMeterData | null
}

export function MarketMeter({ data }: MarketMeterProps) {
  const score = data?.score ?? 50
  const color = data?.color || "#6366f1"
  const mood = data?.mood_label || "Loading Market Data…"

  const fillOffset = ARC_LENGTH * (1 - score / 100)
  const needleDeg = -90 + (score / 100) * 180

  const niftyPrice = data?.nifty_price != null ? data.nifty_price.toLocaleString("en-IN") : "—"
  const change = data?.nifty_change_pct
  const vix = data?.vix_value

  return (
    <div className="px-5 pt-6 md:px-10">
      <div
        className="flex flex-col items-center gap-6 rounded-2xl border bg-surface p-6 md:flex-row md:gap-10"
        style={{ borderColor: color + "44" }}
      >
        {/* Gauge */}
        <div className="relative w-[200px] shrink-0">
          <svg viewBox="0 0 180 100" className="w-full">
            <path
              d={ARC_PATH}
              fill="none"
              stroke="var(--color-border)"
              strokeWidth={14}
              strokeLinecap="round"
            />
            <path
              d={ARC_PATH}
              fill="none"
              stroke={color}
              strokeWidth={14}
              strokeLinecap="round"
              strokeDasharray={ARC_LENGTH}
              strokeDashoffset={fillOffset}
              style={{ transition: "stroke-dashoffset 0.8s ease, stroke 0.4s ease" }}
            />
          </svg>
          {/* Needle */}
          <div
            className="absolute bottom-2.5 left-1/2 h-[64px] w-[3px] origin-bottom rounded-full bg-foreground"
            style={{
              transform: `translateX(-50%) rotate(${needleDeg}deg)`,
              transition: "transform 0.8s cubic-bezier(0.16,1,0.3,1)",
            }}
          />
          <div
            className="absolute left-1/2 top-[42px] -translate-x-1/2 text-3xl font-extrabold"
            style={{ color }}
          >
            {data?.score ?? "—"}
          </div>
          <div className="mt-1 flex justify-between px-1 text-xs font-medium text-muted">
            <span>Fear</span>
            <span>Greed</span>
          </div>
        </div>

        {/* Info */}
        <div className="flex-1">
          <div className="flex items-center gap-2.5">
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{ background: color, boxShadow: `0 0 12px ${color}` }}
            />
            <span className="text-lg font-bold" style={{ color }}>
              {mood}
            </span>
          </div>

          <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
            <Detail label="Nifty 50" value={niftyPrice} />
            <Detail
              label="Daily Change"
              value={change != null ? `${change >= 0 ? "+" : ""}${change.toFixed(2)}%` : "—"}
              valueClass={change != null ? (change >= 0 ? "text-invest" : "text-skip") : ""}
            />
            <Detail
              label="India VIX"
              value={vix != null ? vix.toFixed(2) : "—"}
              valueClass={vix != null ? (vix < 16 ? "text-invest" : "text-skip") : ""}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

function Detail({
  label,
  value,
  valueClass = "",
}: {
  label: string
  value: string
  valueClass?: string
}) {
  return (
    <div className="rounded-xl border border-border bg-white/[0.01] px-4 py-3">
      <div className="text-xs text-muted">{label}</div>
      <div className={`mt-1 text-base font-bold ${valueClass}`}>{value}</div>
    </div>
  )
}
