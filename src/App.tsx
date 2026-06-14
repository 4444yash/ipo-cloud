import { useMemo, useState } from "react"
import useSWR from "swr"
import { Info, AlertCircle } from "lucide-react"
import type { Ipo, FilterTab, SortCriteria } from "./types"
import { fetchToday, fetchScorecard, fetchMarketMeter, triggerRefresh } from "./lib/api"
import { filterAndSortIpos } from "./lib/logic"
import { Header } from "./components/Header"
import { StatsBar } from "./components/StatsBar"
import { MarketMeter } from "./components/MarketMeter"
import { PaywallBanner } from "./components/PaywallBanner"
import { ControlPanel } from "./components/ControlPanel"
import { IpoGrid } from "./components/IpoGrid"
import { CheatSheet } from "./components/CheatSheet"
import { Scorecard } from "./components/Scorecard"
import { DetailModal } from "./components/DetailModal"

const REFRESH_MS = 5 * 60 * 1000
const UPI_ID = (import.meta.env.VITE_UPI_ID as string) || "yourname@upi"
const VIP_STORAGE_KEY = "vip_key"

export default function App() {
  const [vipKey, setVipKey] = useState(() => localStorage.getItem(VIP_STORAGE_KEY) || "")
  const [keyError, setKeyError] = useState("")
  const [tab, setTab] = useState<FilterTab>("all")
  const [search, setSearch] = useState("")
  const [sort, setSort] = useState<SortCriteria>("date-desc")
  const [selected, setSelected] = useState<Ipo | null>(null)
  const [syncing, setSyncing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState("Fetching data…")

  const todaySWR = useSWR(["today", vipKey], () => fetchToday(vipKey), {
    refreshInterval: REFRESH_MS,
    onSuccess: () => {
      const now = new Date().toLocaleTimeString("en-IN", {
        hour: "2-digit",
        minute: "2-digit",
      })
      setLastUpdated(`Updated at ${now}`)
    },
  })

  const scorecardSWR = useSWR("scorecard", fetchScorecard, { refreshInterval: REFRESH_MS })
  const meterSWR = useSWR("meter", fetchMarketMeter, { refreshInterval: REFRESH_MS })

  const ipos = todaySWR.data?.ipos ?? []
  const usingSampleData = todaySWR.data?.usingSampleData ?? false
  const isLocked = ipos.some((d) => d.decision_label === "LOCKED")
  const isVip = !isLocked && vipKey.length > 0

  const stats = useMemo(
    () => ({
      total: ipos.length,
      invest: ipos.filter((d) => d.decision_label === "INVEST").length,
      skip: ipos.filter((d) => d.decision_label === "SKIP").length,
    }),
    [ipos],
  )

  const visibleIpos = useMemo(
    () => filterAndSortIpos(ipos, tab, search, sort),
    [ipos, tab, search, sort],
  )

  function handleActivate(key: string) {
    setKeyError("")
    localStorage.setItem(VIP_STORAGE_KEY, key)
    setVipKey(key)
    // Revalidate against the new key; if it stays locked we surface an error.
    fetchToday(key).then((res) => {
      const stillLocked = res.ipos.some((d) => d.decision_label === "LOCKED")
      if (stillLocked) {
        setKeyError("Invalid or expired VIP Access Key. Please double-check your entry.")
        localStorage.removeItem(VIP_STORAGE_KEY)
        setVipKey("")
      }
    })
  }

  async function handleSync() {
    setSyncing(true)
    await triggerRefresh()
    setTimeout(() => {
      todaySWR.mutate()
      scorecardSWR.mutate()
      meterSWR.mutate()
      setSyncing(false)
    }, 1500)
  }

  return (
    <main className="min-h-screen pb-10">
      <Header
        isVip={isVip}
        vipKey={vipKey}
        lastUpdated={lastUpdated}
        syncing={syncing}
        onSync={handleSync}
      />

      {usingSampleData && (
        <div className="mx-5 mt-6 flex items-center gap-2 rounded-xl border border-accent/30 bg-accent/10 px-4 py-3 text-sm text-foreground md:mx-10">
          <Info size={16} className="shrink-0 text-accent" />
          Demo data: the FastAPI backend is unreachable, so representative sample IPOs are shown.
          Connect the Python server to see live predictions.
        </div>
      )}

      <StatsBar total={stats.total} invest={stats.invest} skip={stats.skip} />

      <MarketMeter data={meterSWR.data ?? null} />

      {isLocked && (
        <>
          <PaywallBanner upiId={UPI_ID} onActivate={handleActivate} />
          {keyError && (
            <div className="mx-5 mt-3 flex items-center gap-2 rounded-xl border border-skip/30 bg-skip/10 px-4 py-3 text-sm text-skip md:mx-10">
              <AlertCircle size={16} className="shrink-0" />
              {keyError}
            </div>
          )}
        </>
      )}

      <ControlPanel
        tab={tab}
        search={search}
        sort={sort}
        onTab={setTab}
        onSearch={setSearch}
        onSort={setSort}
      />

      <IpoGrid
        ipos={visibleIpos}
        loading={todaySWR.isLoading}
        empty={!todaySWR.isLoading && ipos.length === 0}
        onSelect={setSelected}
      />

      <CheatSheet />

      <Scorecard rows={scorecardSWR.data ?? []} loading={scorecardSWR.isLoading} />

      <DetailModal ipo={selected} onClose={() => setSelected(null)} />
    </main>
  )
}
