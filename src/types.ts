// Mirrors the rows returned by the FastAPI endpoints in app.py.
// Numeric fields can come back as null/"" from pandas, so they are optional.

export type DecisionLabel = "INVEST" | "SKIP" | "LOCKED"
export type IpoType = "Mainboard" | "SME" | string
export type IpoStatus = "active" | "closed" | string

export interface Ipo {
  ipo_name: string
  predicted_probability?: number | null
  gmp_pct?: number | null
  gmp?: number | null
  final_decision?: number | null
  decision_label?: DecisionLabel | null
  predicted_at?: string | null
  listing_date?: string | null
  open_date?: string | null
  close_date?: string | null
  subscription_x?: number | null
  ipo_price?: number | null
  lot_size?: number | null
  ipo_size_cr?: number | null
  has_anchor?: number | null
  ipo_type?: IpoType | null
  status?: IpoStatus | null
}

export interface ScorecardRow {
  ipo_name: string
  decision_label?: DecisionLabel | null
  gmp_pct?: number | null
  actual_gain_pct?: number | null
  was_correct?: number | null
  model_accuracy?: number | null
}

export interface MarketMeter {
  score?: number | null
  mood_label?: string | null
  color?: string | null
  nifty_price?: number | null
  nifty_change_pct?: number | null
  vix_value?: number | null
  updated_at?: string | null
}

export type SortCriteria =
  | "date-desc"
  | "date-asc"
  | "prob-desc"
  | "prob-asc"
  | "gmp-desc"
  | "sub-desc"

export type FilterTab = "all" | "Mainboard" | "SME" | "Closed"
