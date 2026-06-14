import { useState } from "react"
import { Lock, Smartphone } from "lucide-react"

interface PaywallBannerProps {
  upiId: string
  onActivate: (key: string) => void
}

export function PaywallBanner({ upiId, onActivate }: PaywallBannerProps) {
  const [value, setValue] = useState("")

  function submit() {
    const key = value.trim()
    if (!key) return
    onActivate(key)
  }

  return (
    <div className="px-5 pt-6 md:px-10">
      <div className="flex flex-col gap-5 rounded-2xl border border-accent/30 bg-gradient-to-br from-accent/10 to-violet/5 p-6 md:flex-row md:items-center md:justify-between">
        <div className="max-w-xl">
          <div className="flex items-center gap-2 text-lg font-bold">
            <Lock size={18} className="text-accent" />
            Unlock Neural Network Predictions
          </div>
          <p className="mt-2 text-sm leading-relaxed text-muted">
            Get instant access to AI Investment Probability Ratings and exact skip/invest
            decision tags. Send <strong className="text-foreground">{"\u20B9"}299/month</strong> to
            our UPI ID, then enter your activated access key.
          </p>
        </div>

        <div className="flex flex-col gap-3">
          <div className="inline-flex items-center gap-2 rounded-lg border border-border bg-surface px-3 py-2 text-sm">
            <Smartphone size={15} className="text-accent" />
            GPay / UPI ID: <strong className="text-foreground">{upiId}</strong>
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submit()}
              placeholder="Enter Access Key..."
              aria-label="VIP access key"
              className="min-w-0 flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground outline-none placeholder:text-muted focus:border-accent"
            />
            <button
              onClick={submit}
              className="rounded-lg bg-accent px-5 py-2 text-sm font-semibold text-white transition hover:bg-accent/85"
            >
              Unlock
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
