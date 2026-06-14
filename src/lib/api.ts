import type { Ipo, ScorecardRow, MarketMeter } from "../types"
import { SAMPLE_IPOS, SAMPLE_SCORECARD, SAMPLE_MARKET_METER } from "./sampleData"

// The real FastAPI endpoints are called with relative paths (proxied to
// the Python backend during local dev). If the backend is unreachable or
// returns an error payload, we fall back to representative sample data so
// the UI remains fully visible. `usingSampleData` lets the UI surface a
// small "demo data" notice.

export interface TodayResult {
  ipos: Ipo[]
  usingSampleData: boolean
}

function isErrorPayload(data: unknown): boolean {
  return (
    data == null ||
    (typeof data === "object" && !Array.isArray(data) && "error" in (data as object))
  )
}

export async function fetchToday(key: string): Promise<TodayResult> {
  try {
    const res = await fetch(`/today?key=${encodeURIComponent(key)}`)
    if (!res.ok) throw new Error(`API returned ${res.status}`)
    const data = await res.json()
    if (isErrorPayload(data)) throw new Error("Backend not initialized")
    return { ipos: data as Ipo[], usingSampleData: false }
  } catch {
    // Fallback: when there is no saved VIP key, emulate the freemium
    // paywall by locking the ML signals, exactly like the backend does.
    const isVip = key.trim().length > 0
    const ipos = SAMPLE_IPOS.map((ipo) =>
      isVip
        ? ipo
        : {
            ...ipo,
            decision_label: "LOCKED" as const,
            predicted_probability: 0,
            final_decision: 0,
          },
    )
    return { ipos, usingSampleData: true }
  }
}

export async function fetchScorecard(): Promise<ScorecardRow[]> {
  try {
    const res = await fetch("/scorecard_data")
    if (!res.ok) throw new Error(`API returned ${res.status}`)
    const data = await res.json()
    if (isErrorPayload(data)) throw new Error("Backend not initialized")
    return data as ScorecardRow[]
  } catch {
    return SAMPLE_SCORECARD
  }
}

export async function fetchMarketMeter(): Promise<MarketMeter | null> {
  try {
    const res = await fetch("/market_meter_data")
    if (!res.ok) throw new Error(`API returned ${res.status}`)
    const data = await res.json()
    if (isErrorPayload(data)) throw new Error("Backend not initialized")
    const rows = data as MarketMeter[]
    return rows.length ? rows[0] : null
  } catch {
    return SAMPLE_MARKET_METER
  }
}

export async function triggerRefresh(): Promise<void> {
  try {
    await fetch("/refresh-pipeline", { method: "POST" })
  } catch {
    // No-op in preview; the caller re-fetches regardless.
  }
}
