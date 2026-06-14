import { Search } from "lucide-react"
import type { FilterTab, SortCriteria } from "../types"

const TABS: { id: FilterTab; label: string }[] = [
  { id: "all", label: "All IPOs" },
  { id: "Mainboard", label: "Mainboard" },
  { id: "SME", label: "SME" },
  { id: "Closed", label: "Recently Closed" },
]

const SORTS: { value: SortCriteria; label: string }[] = [
  { value: "date-desc", label: "Sort by: Date (Newest)" },
  { value: "date-asc", label: "Sort by: Date (Oldest)" },
  { value: "prob-desc", label: "Sort by: Probability (High to Low)" },
  { value: "prob-asc", label: "Sort by: Probability (Low to High)" },
  { value: "gmp-desc", label: "Sort by: GMP % (Highest)" },
  { value: "sub-desc", label: "Sort by: Subscription (Highest)" },
]

interface ControlPanelProps {
  tab: FilterTab
  search: string
  sort: SortCriteria
  onTab: (t: FilterTab) => void
  onSearch: (s: string) => void
  onSort: (s: SortCriteria) => void
}

export function ControlPanel({
  tab,
  search,
  sort,
  onTab,
  onSearch,
  onSort,
}: ControlPanelProps) {
  return (
    <div className="flex flex-col gap-4 px-5 pt-6 md:flex-row md:items-center md:justify-between md:px-10">
      <div className="flex flex-wrap gap-2" role="tablist" aria-label="IPO filters">
        {TABS.map((t) => {
          const active = t.id === tab
          return (
            <button
              key={t.id}
              role="tab"
              aria-selected={active}
              onClick={() => onTab(t.id)}
              className={`rounded-lg border px-4 py-2 text-sm font-semibold transition ${
                active
                  ? "border-accent bg-accent text-white"
                  : "border-border bg-surface text-muted hover:text-foreground"
              }`}
            >
              {t.label}
            </button>
          )
        })}
      </div>

      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative">
          <Search
            size={16}
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted"
          />
          <input
            type="text"
            value={search}
            onChange={(e) => onSearch(e.target.value)}
            placeholder="Search IPOs by name..."
            aria-label="Search IPOs by name"
            className="w-full rounded-lg border border-border bg-surface py-2 pl-9 pr-3 text-sm text-foreground outline-none placeholder:text-muted focus:border-accent sm:w-60"
          />
        </div>
        <select
          value={sort}
          onChange={(e) => onSort(e.target.value as SortCriteria)}
          aria-label="Sort IPOs"
          className="rounded-lg border border-border bg-surface px-3 py-2 text-sm text-foreground outline-none focus:border-accent"
        >
          {SORTS.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}
