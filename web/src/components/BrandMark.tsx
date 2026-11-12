interface Props {
  className?: string
  /** Dot color; defaults to the brand emerald. */
  dotColor?: string
}

/**
 * Foley mark: two intercut frame layers + a record dot.
 * Layer A (currentColor) is the active cut, layer B (muted) is the one
 * behind it, the dot is the playhead. Pure geometry — no gradients.
 */
export function BrandMark({ className, dotColor = "#10B981" }: Props) {
  return (
    <svg
      viewBox="0 0 24 24"
      className={className}
      fill="none"
      aria-hidden="true"
      role="img"
    >
      {/* layer B — the cut behind */}
      <g
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        opacity="0.45"
      >
        <path d="M16.5 2.9 H18.8 Q21.1 2.9 21.1 5.2 V7.5" />
        <path d="M7.5 21.1 H5.2 Q2.9 21.1 2.9 18.8 V16.5" />
      </g>
      {/* layer A — the active cut */}
      <g stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
        <path d="M2.9 7.5 V5.2 Q2.9 2.9 5.2 2.9 H7.5" />
        <path d="M16.5 21.1 H18.8 Q21.1 21.1 21.1 18.8 V16.5" />
      </g>
      {/* playhead */}
      <circle cx="12" cy="12" r="2.7" fill={dotColor} />
    </svg>
  )
}
