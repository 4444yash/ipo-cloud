import { Target, CreditCard, AlertTriangle, Clock, Lightbulb } from "lucide-react"
import type { LucideIcon } from "lucide-react"

interface Tip {
  icon: LucideIcon
  title: string
  body: string
}

const TIPS: Tip[] = [
  {
    icon: Target,
    title: 'Tick "Cut-off Price"',
    body: 'Always select the "Cut-off Price" box. If you bid below the final issue price on popular IPOs, your application gets rejected immediately.',
  },
  {
    icon: CreditCard,
    title: "PAN Name Match",
    body: "Your Demat account PAN name must match your Bank/UPI account name. Third-party payments (e.g. paying with a spouse's UPI) get auto-rejected.",
  },
  {
    icon: AlertTriangle,
    title: "SME Capital Warning",
    body: "SME IPOs require \u20B91.2L+ minimum capital and must be traded in full lots (no single shares). Only apply if you understand the liquidity risks.",
  },
  {
    icon: Clock,
    title: "Bidding Timing",
    body: "Check final subscription trends and our AI predictions on the last day of bidding (Day 3) before applying to avoid sudden drops.",
  },
]

export function CheatSheet() {
  return (
    <section className="px-5 pt-10 md:px-10">
      <h2 className="mb-5 flex items-center gap-2 text-xl font-bold">
        <Lightbulb className="text-accent" size={22} />
        Smart IPO Bidding Cheat Sheet (Beginners)
      </h2>
      <div className="grid grid-cols-1 gap-5 rounded-2xl border border-border bg-surface p-6 sm:grid-cols-2 lg:grid-cols-4">
        {TIPS.map((tip) => {
          const Icon = tip.icon
          return (
            <div
              key={tip.title}
              className="rounded-xl border border-white/[0.03] bg-white/[0.01] p-4"
            >
              <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-violet">
                <Icon size={16} /> {tip.title}
              </h3>
              <p className="text-sm leading-relaxed text-muted">{tip.body}</p>
            </div>
          )
        })}
      </div>
    </section>
  )
}
