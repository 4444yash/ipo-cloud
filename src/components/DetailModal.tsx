import { useEffect } from "react"
import { X, TrendingUp, TrendingDown, Lightbulb } from "lucide-react"
import type { Ipo } from "../types"
import { ProbRing } from "./ProbRing"
import { Badge } from "./Badge"
import {
  generateAIVerdict,
  getSmartTip,
  getExpectedProfitText,
  getDemandMeter,
  formatInr,
} from "../lib/logic"

interface DetailModalProps {
  ipo: Ipo | null
  onClose: () => void
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 text-sm">
      <span className="text-muted">{label}</span>
      <strong className="text-right">{value}</strong>
    </div>
  )
}

function SectionTitle({ children, className = "" }: { children: string; className?: string }) {
  return (
    <div className={`mb-3 text-sm font-bold uppercase tracking-wide ${className}`}>{children}</div>
  )
}

export function DetailModal({ ipo, onClose }: DetailModalProps) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose()
    }
    if (ipo) {
      document.addEventListener("keydown", onKey)
      document.body.style.overflow = "hidden"
    }
    return () => {
      document.removeEventListener("keydown", onKey)
      document.body.style.overflow = ""
    }
  }, [ipo, onClose])

  if (!ipo) return null

  const label = ipo.decision_label || "SKIP"
  const isInvest = label === "INVEST"
  const isLocked = label === "LOCKED"
  const prob = ipo.predicted_probability ?? 0
  const type = ipo.ipo_type || "Mainboard"

  const gmpPct = ipo.gmp_pct != null ? `${ipo.gmp_pct.toFixed(1)}%` : "—"
  const price = ipo.ipo_price != null ? `\u20B9${ipo.ipo_price}` : "—"
  const gmpRs = ipo.gmp != null ? `\u20B9${ipo.gmp}` : "—"
  const lot = ipo.lot_size
    ? `${ipo.lot_size} shares (\u20B9${formatInr(ipo.lot_size * (ipo.ipo_price || 0))})`
    : "—"
  const size = ipo.ipo_size_cr ? `\u20B9${ipo.ipo_size_cr} Cr` : "—"

  const expectedProfit = isLocked ? "LOCKED (AI)" : getExpectedProfitText(ipo)
  const demand = getDemandMeter(ipo.subscription_x).text

  return (
    <div
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/70 p-4 backdrop-blur-sm sm:items-center"
      role="dialog"
      aria-modal="true"
      aria-label={`${ipo.ipo_name} details`}
    >
      <div className="animate-modal-pop my-4 w-full max-w-2xl rounded-2xl border border-border bg-surface shadow-2xl">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 border-b border-border p-5">
          <div>
            <div className="text-xl font-extrabold">{ipo.ipo_name}</div>
            <div className="mt-2 flex items-center gap-2">
              <Badge variant={type === "SME" ? "sme" : "mainboard"}>{type}</Badge>
              <Badge variant={isInvest ? "invest" : "skip"}>
                {isInvest ? <TrendingUp size={12} /> : <TrendingDown size={12} />} {label}
              </Badge>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            className="rounded-lg border border-border p-2 text-muted transition hover:text-foreground"
          >
            <X size={18} />
          </button>
        </div>

        <div className="flex flex-col gap-6 p-5">
          {/* Verdict banner */}
          <div
            className={`flex items-center gap-4 rounded-xl border p-4 ${
              isInvest ? "border-invest/30 bg-invest/10" : "border-skip/30 bg-skip/10"
            }`}
          >
            <ProbRing prob={prob} label={label} size={64} />
            <div>
              <div className="text-lg font-bold">
                {isInvest ? "INVEST Recommendation" : "SKIP Signal"}
              </div>
              <div className="text-sm text-muted">
                Neural Network Confidence: {Math.round(prob * 100)}%
              </div>
            </div>
          </div>

          {/* AI analysis */}
          <div>
            <SectionTitle className="text-accent">AI Signal Analysis</SectionTitle>
            <div
              className="text-sm leading-relaxed text-foreground/90 [&_strong]:text-foreground"
              dangerouslySetInnerHTML={{ __html: generateAIVerdict(ipo) }}
            />
          </div>

          {/* Financial metrics */}
          <div>
            <SectionTitle className="text-accent">IPO Details & Financial Metrics</SectionTitle>
            <div className="flex flex-col gap-3">
              <div className="rounded-xl border border-border bg-white/[0.01] p-3">
                <div className="text-xs text-muted">Expected Listing Profit</div>
                <div className="mt-0.5 text-sm font-bold text-gold">{expectedProfit}</div>
              </div>
              <div className="rounded-xl border border-border bg-white/[0.01] p-3">
                <div className="text-xs text-muted">Demand Meter</div>
                <div className="mt-0.5 text-sm font-bold text-accent">{demand}</div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <ModalMetric label="GMP (Per Share)" value={gmpRs} valueClass="text-gold" />
                <ModalMetric label="GMP %" value={gmpPct} valueClass="text-gold" />
                <ModalMetric label="IPO Price" value={price} />
                <ModalMetric label="IPO Size" value={size} />
              </div>
              <ModalMetric label="Lot Size / Min Application" value={lot} />
            </div>
          </div>

          {/* Timeline */}
          <div>
            <SectionTitle className="text-accent">Timeline & Info</SectionTitle>
            <div className="flex flex-col gap-2.5 rounded-xl border border-border bg-white/[0.01] p-4">
              <Row label="Offer Open Date:" value={ipo.open_date || "—"} />
              <Row label="Offer Close Date:" value={ipo.close_date || "—"} />
              <Row label="Expected Listing Date:" value={ipo.listing_date || "—"} />
              <Row
                label="Institutional Backing:"
                value={ipo.has_anchor ? "Anchor Book Present" : "No Anchor Segment"}
              />
            </div>
          </div>

          {/* Smart tip */}
          <div>
            <SectionTitle className="flex items-center gap-1.5 text-violet">
              Smart Bidding Tip for Beginners
            </SectionTitle>
            <div className="flex gap-3 rounded-xl border border-violet/20 bg-violet/5 p-4">
              <Lightbulb size={18} className="mt-0.5 shrink-0 text-violet" />
              <div
                className="text-sm leading-relaxed text-foreground/90 [&_strong]:text-foreground"
                dangerouslySetInnerHTML={{ __html: getSmartTip(ipo) }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function ModalMetric({
  label,
  value,
  valueClass = "",
}: {
  label: string
  value: string
  valueClass?: string
}) {
  return (
    <div className="rounded-xl border border-border bg-white/[0.01] p-3">
      <div className="text-xs text-muted">{label}</div>
      <div className={`mt-0.5 text-sm font-bold ${valueClass}`}>{value}</div>
    </div>
  )
}
