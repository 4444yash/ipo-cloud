import { TrendingUp, RefreshCw, Crown } from "lucide-react"

interface HeaderProps {
  isVip: boolean
  vipKey: string
  lastUpdated: string
  syncing: boolean
  onSync: () => void
}

export function Header({ isVip, vipKey, lastUpdated, syncing, onSync }: HeaderProps) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-border bg-gradient-to-br from-surface-raised to-background px-5 py-6 md:px-10">
      <div className="flex items-center gap-3.5">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-accent to-violet text-white shadow-lg shadow-accent/30">
          <TrendingUp size={22} />
        </div>
        <div>
          <h1 className="text-xl font-extrabold tracking-tight">IPO Predictor</h1>
          <p className="text-sm text-muted">Live ML-powered investment signals</p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3 text-sm">
        {isVip && (
          <span
            title={`Access Key: ${vipKey}`}
            className="inline-flex items-center gap-1.5 rounded-full border border-gold/40 bg-gold/12 px-3 py-1.5 font-semibold text-gold"
          >
            <Crown size={14} /> VIP Active
          </span>
        )}
        <span className="text-muted">{lastUpdated}</span>
        <button
          onClick={onSync}
          disabled={syncing}
          className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2 font-semibold text-white transition hover:bg-accent/85 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <RefreshCw size={16} className={syncing ? "animate-spin-slow" : ""} />
          {syncing ? "Syncing..." : "Sync Latest Data"}
        </button>
      </div>
    </header>
  )
}
