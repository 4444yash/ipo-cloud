import { BarChart3, Target, CheckCircle2, XCircle } from "lucide-react"
import type { ScorecardRow } from "../types"
import { Badge } from "./Badge"
import { Spinner } from "./Spinner"

interface ScorecardProps {
  rows: ScorecardRow[]
  loading: boolean
}

export function Scorecard({ rows, loading }: ScorecardProps) {
  const accuracy =
    rows.length && rows[0].model_accuracy != null
      ? `${rows[0].model_accuracy.toFixed(1)}%`
      : "—"

  return (
    <section className="px-5 py-10 md:px-10">
      <h2 className="mb-5 flex items-center gap-2 text-xl font-bold">
        <BarChart3 className="text-accent" size={22} />
        Past Performance Scorecard
      </h2>

      {loading ? (
        <Spinner label="Loading past performance…" />
      ) : !rows.length ? (
        <div className="rounded-2xl border border-border bg-surface p-10 text-center text-muted">
          No historical data found.
        </div>
      ) : (
        <>
          <div className="mb-4 flex items-center gap-2 border-b border-border pb-3 text-base font-semibold text-accent">
            <Target size={18} /> INVEST Accuracy: {accuracy}
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {rows.map((row, i) => {
              const label = row.decision_label || "SKIP"
              const isInvest = label === "INVEST"
              const correct = row.was_correct === 1
              const gain = row.actual_gain_pct != null ? `${row.actual_gain_pct.toFixed(1)}%` : "—"
              const gainUp = (row.actual_gain_pct ?? 0) > 0
              return (
                <div
                  key={`${row.ipo_name}-${i}`}
                  className={`rounded-2xl border border-border border-l-4 bg-surface p-5 ${
                    correct ? "border-l-invest" : "border-l-skip"
                  }`}
                >
                  <div className="text-sm font-bold">{row.ipo_name}</div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <Badge variant={isInvest ? "invest" : "skip"}>Predicted: {label}</Badge>
                    <Badge variant={correct ? "invest" : "skip"}>
                      {correct ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
                      {correct ? "CORRECT" : "MISS"}
                    </Badge>
                  </div>
                  <div className="mt-4 grid grid-cols-2 gap-2.5">
                    <div className="rounded-lg border border-border bg-white/[0.01] px-3 py-2.5">
                      <div className="text-xs text-muted">GMP at IPO</div>
                      <div className="mt-0.5 text-sm font-bold">
                        {row.gmp_pct != null ? `${row.gmp_pct.toFixed(1)}%` : "—"}
                      </div>
                    </div>
                    <div className="rounded-lg border border-border bg-white/[0.01] px-3 py-2.5">
                      <div className="text-xs text-muted">Actual Listing Gain</div>
                      <div
                        className={`mt-0.5 text-sm font-bold ${gainUp ? "text-invest" : "text-skip"}`}
                      >
                        {gain}
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}
    </section>
  )
}
