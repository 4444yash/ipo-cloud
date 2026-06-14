import type { Ipo, FilterTab, SortCriteria } from "../types"

// ── Faithful ports of the helper functions from the original template ──

export function formatInr(n: number): string {
  return n.toLocaleString("en-IN")
}

export function getExpectedProfitText(ipo: Ipo): string {
  if (ipo.gmp == null || ipo.lot_size == null || ipo.gmp_pct == null) {
    return "—"
  }
  const profit = Math.round(ipo.gmp * ipo.lot_size)
  const sign = profit >= 0 ? "+" : ""
  return `Expected Listing Profit: ${sign}₹${formatInr(profit)} per lot (${sign}${ipo.gmp_pct.toFixed(1)}% gain)`
}

export function getDemandMeter(sub: number | null | undefined): {
  text: string
  speed: string
} {
  if (sub == null || isNaN(sub) || sub <= 0) return { text: "—", speed: "—" }

  let speed = "Low"
  if (sub >= 25) speed = "Extreme"
  else if (sub >= 10) speed = "Very High"
  else if (sub >= 3) speed = "High"
  else if (sub >= 1.1) speed = "Healthy"
  else if (sub >= 0.9) speed = "Fully Subscribed"
  else speed = "Under-subscribed"

  const bidRatio = Math.round(sub)
  const text =
    bidRatio >= 1
      ? `${speed} Demand (${bidRatio} bidding for every 1 share)`
      : `${speed} Demand (${sub.toFixed(1)}x demand)`
  return { text, speed }
}

// Returns HTML markup (internally generated, no user input) describing the
// neural-network verdict. Mirrors generateAIVerdict() from the template.
export function generateAIVerdict(ipo: Ipo): string {
  const gmpPct = ipo.gmp_pct ?? 0
  const sub = ipo.subscription_x ?? 0
  const size = ipo.ipo_size_cr ?? 0
  const anchor = ipo.has_anchor === 1
  const prob = ipo.predicted_probability ?? 0
  const decision = ipo.decision_label || "SKIP"

  let analysis = ""

  if (decision === "INVEST") {
    analysis += `<strong>AI Neural Network Verdict:</strong> Our ML model recommends an <strong>INVEST</strong> signal for <strong>${ipo.ipo_name}</strong> with a probability rating of <strong>${Math.round(prob * 100)}%</strong>.<br/><br/>`
    analysis += `<strong>Key Strength Factors:</strong><br/>`
    let bulletCount = 0

    if (gmpPct >= 15) {
      analysis += `&bull; <strong>Strong Grey Market Demand:</strong> The GMP is currently sitting at a premium of <strong>${gmpPct.toFixed(1)}%</strong> over the issue price, suggesting very high listings day gains expectation.<br/>`
      bulletCount++
    } else if (gmpPct >= 5) {
      analysis += `&bull; <strong>Moderate Grey Market Demand:</strong> A GMP premium of <strong>${gmpPct.toFixed(1)}%</strong> indicates stable demand and low listing risk.<br/>`
      bulletCount++
    }

    if (sub >= 5.0) {
      analysis += `&bull; <strong>Heavy Subscription:</strong> The IPO is subscribed <strong>${sub.toFixed(1)}x</strong>, showing excellent subscription velocity and post-listing buying support.<br/>`
      bulletCount++
    } else if (sub >= 1.5) {
      analysis += `&bull; <strong>Subscribed:</strong> The subscription at <strong>${sub.toFixed(1)}x</strong> is healthy enough to clear the issue.<br/>`
      bulletCount++
    }

    if (anchor) {
      analysis += `&bull; <strong>Anchor Book Allocated:</strong> Confirmed presence of anchor institutional investors indicates strong institutional confidence and validates the company's valuation.<br/>`
      bulletCount++
    }

    if (size > 0 && size < 500) {
      analysis += `&bull; <strong>Tight Supply:</strong> With a small issue size of <strong>₹${size} Cr</strong>, this IPO is prone to high demand squeeze and potential post-listing surge.<br/>`
      bulletCount++
    }

    if (bulletCount === 0) {
      analysis += `&bull; The Neural Network detected complex historical features indicating a high listing success probability based on similar historical IPO profiles.<br/>`
    }
  } else {
    analysis += `<strong>AI Neural Network Verdict:</strong> Our ML model recommends a <strong>SKIP</strong> signal for <strong>${ipo.ipo_name}</strong> (probability rating: <strong>${Math.round(prob * 100)}%</strong>).<br/><br/>`
    analysis += `<strong>Risk Warning Factors:</strong><br/>`
    let bulletCount = 0

    if (gmpPct < 5) {
      analysis += `&bull; <strong>Negligible Grey Market Premium:</strong> The GMP is extremely low or negative at <strong>${gmpPct.toFixed(1)}%</strong>, which carries a severe listing-day discount risk.<br/>`
      bulletCount++
    }

    if (sub < 1.5) {
      analysis += `&bull; <strong>Poor Subscription Interest:</strong> With a subscription rate of only <strong>${sub.toFixed(1)}x</strong>, the market is showing weak subscription velocity, increasing listing-day risk.<br/>`
      bulletCount++
    }

    if (!anchor) {
      analysis += `&bull; <strong>No Anchor Support:</strong> Lack of confirmed anchor institutional backing suggests lower confidence from institutional managers.<br/>`
      bulletCount++
    }

    if (size >= 1500) {
      analysis += `&bull; <strong>Large Market Supply:</strong> The issue size of <strong>₹${size} Cr</strong> is massive. Large supply makes it harder for the share price to pop significantly on listing day unless backed by extreme demand.<br/>`
      bulletCount++
    }

    if (bulletCount === 0) {
      analysis += `&bull; The Neural Network flagged this IPO as carrying higher risks of negative listing gains based on similar historical profiles.<br/>`
    }
  }

  return analysis
}

export function getSmartTip(ipo: Ipo): string {
  const isSme = (ipo.ipo_type || "Mainboard") === "SME"
  const isClosed = ipo.status === "closed"

  if (isClosed) {
    return `<strong>Listing Day Panic Warning:</strong> Bidding is already closed for this IPO. If you applied and got allotted shares, do not trade in the 9:00 AM to 9:45 AM pre-open session on listing day. It's highly volatile. Wait until the market stabilizes around <strong>10:15 AM to 10:30 AM</strong> to make your exit or hold decision.`
  }
  if (isSme) {
    return `<strong>SME Lot Size Warning:</strong> This is an SME (Small and Medium Enterprises) IPO. Unlike normal IPOs (₹15,000 minimum), this requires a minimum capital block of <strong>₹1.2 Lakhs+</strong>. Also, you must trade in full lots (cannot sell single shares later). Recommended only if you have high surplus capital.`
  }
  return `<strong>Tick "Cut-off Price":</strong> Always select the <strong>'Cut-off Price'</strong> checkbox when submitting your bid on your broker app (Zerodha, Groww, AngelOne, etc.). Since this IPO is in demand, bidding at a lower price band will disqualify your application instantly. Also, ensure your UPI payment name matches your PAN card name.`
}

// Mirrors onFilterChange() filtering + sorting from the template.
export function filterAndSortIpos(
  ipos: Ipo[],
  tab: FilterTab,
  search: string,
  sort: SortCriteria,
): Ipo[] {
  const query = search.trim().toLowerCase()

  const filtered = ipos.filter((ipo) => {
    const status = ipo.status || "active"
    if (tab === "Closed") {
      if (status !== "closed") return false
    } else {
      if (status === "closed") return false
      if (tab !== "all") {
        const type = ipo.ipo_type || "Mainboard"
        if (type.toLowerCase() !== tab.toLowerCase()) return false
      }
    }
    if (query) return ipo.ipo_name.toLowerCase().includes(query)
    return true
  })

  const sorted = [...filtered].sort((a, b) => {
    switch (sort) {
      case "prob-desc":
        return (b.predicted_probability ?? 0) - (a.predicted_probability ?? 0)
      case "prob-asc":
        return (a.predicted_probability ?? 0) - (b.predicted_probability ?? 0)
      case "gmp-desc":
        return (b.gmp_pct ?? 0) - (a.gmp_pct ?? 0)
      case "sub-desc":
        return (b.subscription_x ?? 0) - (a.subscription_x ?? 0)
      case "date-asc":
        return (a.listing_date || "").localeCompare(b.listing_date || "")
      case "date-desc":
      default:
        return (b.listing_date || "").localeCompare(a.listing_date || "")
    }
  })

  return sorted
}
