import { Lock, TrendingUp, TrendingDown, CheckCircle2, XCircle } from "lucide-react"
import type { Ipo } from "../types"
import { ProbRing } from "./ProbRing"
import { Badge } from "./Badge"

interface IpoCardProps {
  ipo: Ipo
  onClick: () => void
}

function Metric({
  label,
  value,
  valueClass = "",
}: {
  label: string
  value: string
  valueClass?: string
}) {
  return (
    <div className="rounded-lg border border-border bg-white/[0.01] px-3 py-2.5">
      <div className="text-xs text-muted">{label}</div>
      <div className={`mt-0.5 text-base font-bold ${valueClass}`}>{value}</div>
    </div>
  )
}

export function IpoCard({ ipo, onClick }: IpoCardProps) {
  const label = ipo.decision_label || "SKIP"
  const isLocked = label === "LOCKED"
  const isInvest = label === "INVEST"
  const prob = ipo.predicted_probability ?? 0

  const gmp = ipo.gmp_pct != null ? `${ipo.gmp_pct.toFixed(1)}%` : "—"
  const sub = ipo.subscription_x != null ? `${ipo.subscription_x.toFixed(1)}x` : "—"
  const price = ipo.ipo_price != null ? `\u20B9${ipo.ipo_price}` : "—"
  const gmpRs = ipo.gmp != null ? `\u20B9${ipo.gmp}` : "—"

  const type = ipo.ipo_type || "Mainboard"
  const isClosed = ipo.status === "closed"

  const accentBorder = isLocked
    ? "border-l-border"
    : isInvest
      ? "border-l-invest"
      : "border-l-skip"

  return (
    <div
      onClick={isLocked ? undefined : onClick}
      role={isLocked ? undefined : "button"}
      tabIndex={isLocked ? undefined : 0}
      onKeyDown={(e) => {
        if (!isLocked && (e.key === "Enter" || e.key === " ")) {
          e.preventDefault()
          onClick()
        }
      }}
      className={`animate-fade-in rounded-2xl border border-border border-l-4 ${accentBorder} bg-surface p-5 transition ${
        isLocked
          ? "opacity-90"
          : "cursor-pointer hover:-translate-y-0.5 hover:border-accent/40 hover:shadow-lg hover:shadow-black/30"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate text-base font-bold">{ipo.ipo_name}</div>
          <div className="mt-2 flex flex-wrap gap-2">
            {isLocked ? (
              <Badge variant="skip">
                <Lock size={12} /> LOCKED (AI)
              </Badge>
            ) : (
              <Badge variant={isInvest ? "invest" : "skip"}>
                {isInvest ? <TrendingUp size={12} /> : <TrendingDown size={12} />} {label}
              </Badge>
            )}
            <Badge variant={type === "SME" ? "sme" : "mainboard"}>{type}</Badge>
            {isClosed && (
              <Badge variant="skip">
                <Lock size={12} /> CLOSED
              </Badge>
            )}
          </div>
        </div>
        {isLocked ? (
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full border border-border text-muted">
            <Lock size={20} />
          </div>
        ) : (
          <ProbRing prob={prob} label={label} />
        )}
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2.5">
        <Metric label="GMP %" value={gmp} valueClass="text-gold" />
        <Metric label="Subscription" value={sub} valueClass="text-accent" />
        <Metric label="IPO Price" value={price} />
        <Metric label="GMP (Per Share)" value={gmpRs} valueClass="text-gold" />
      </div>

      <div className="mt-3.5 inline-flex items-center gap-1.5 rounded-full border border-border bg-white/[0.01] px-3 py-1.5 text-xs text-muted">
        {ipo.has_anchor ? (
          <>
            <CheckCircle2 size={13} className="text-invest" /> Anchor investors
          </>
        ) : (
          <>
            <XCircle size={13} className="text-skip" /> No anchor
          </>
        )}
      </div>

      <div className="mt-3.5 flex flex-wrap gap-x-3 gap-y-1 text-xs leading-relaxed text-muted">
        {ipo.open_date && (
          <span>
            <span className="text-invest">{"\u25CF"}</span> Open: {ipo.open_date}
          </span>
        )}
        {ipo.close_date && (
          <span>
            <span className="text-skip">{"\u25CF"}</span> Close: {ipo.close_date}
          </span>
        )}
        {ipo.listing_date && <span>Listing: {ipo.listing_date}</span>}
      </div>
    </div>
  )
}
