import { Search, Moon } from "lucide-react"
import type { Ipo } from "../types"
import { IpoCard } from "./IpoCard"
import { Spinner } from "./Spinner"

interface IpoGridProps {
  ipos: Ipo[]
  loading: boolean
  empty: boolean
  onSelect: (ipo: Ipo) => void
}

export function IpoGrid({ ipos, loading, empty, onSelect }: IpoGridProps) {
  if (loading) {
    return (
      <div className="px-5 pt-6 md:px-10">
        <Spinner label="Loading predictions…" />
      </div>
    )
  }

  if (empty) {
    return (
      <div className="px-5 pt-6 md:px-10">
        <div className="flex flex-col items-center gap-3 rounded-2xl border border-border bg-surface p-12 text-center text-muted">
          <Moon size={28} />
          <span>No predictions yet for today. Check back after the next pipeline run.</span>
        </div>
      </div>
    )
  }

  if (!ipos.length) {
    return (
      <div className="px-5 pt-6 md:px-10">
        <div className="flex flex-col items-center gap-3 rounded-2xl border border-border bg-surface p-12 text-center text-muted">
          <Search size={28} />
          <span>No matching IPOs found. Try adjusting your filters.</span>
        </div>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-5 px-5 pt-6 md:grid-cols-2 md:px-10 xl:grid-cols-3">
      {ipos.map((ipo, i) => (
        <IpoCard key={`${ipo.ipo_name}-${i}`} ipo={ipo} onClick={() => onSelect(ipo)} />
      ))}
    </div>
  )
}
