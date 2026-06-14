import type { DecisionLabel } from "../types"

const RADIUS = 22
const CIRCUMFERENCE = 2 * Math.PI * RADIUS

interface ProbRingProps {
  prob: number
  label: DecisionLabel
  size?: number
}

// Circular probability gauge, ported from makeRing() in the template.
export function ProbRing({ prob, label, size = 56 }: ProbRingProps) {
  const isInvest = label === "INVEST"
  const color = isInvest ? "var(--color-invest)" : "var(--color-skip)"
  const offset = CIRCUMFERENCE * (1 - prob)
  const center = 28
  const scale = size / 56

  return (
    <div
      className="relative shrink-0"
      style={{ width: size, height: size }}
      role="img"
      aria-label={`Predicted probability ${Math.round(prob * 100)} percent`}
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 56 56"
        className="-rotate-90"
      >
        <circle
          cx={center}
          cy={center}
          r={RADIUS}
          fill="none"
          strokeWidth={4}
          stroke="var(--color-border)"
        />
        <circle
          cx={center}
          cy={center}
          r={RADIUS}
          fill="none"
          strokeWidth={4}
          stroke={color}
          strokeLinecap="round"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      <div
        className="absolute inset-0 flex items-center justify-center font-bold"
        style={{ color, fontSize: 15 * scale }}
      >
        {Math.round(prob * 100)}
        <small style={{ fontSize: 9 * scale, marginLeft: 1 }}>%</small>
      </div>
    </div>
  )
}
