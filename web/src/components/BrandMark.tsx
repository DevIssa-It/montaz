/**
 * Montaz mark — the assembled cut.
 * Two intercut bracket layers (the montage) frame a single clip: many
 * cuts, assembled into one story. The center clip carries the brand
 * accent. Always set the wordmark lowercase — the spelling is the brand.
 * Pure geometry — no gradients, no glow.
 */
interface Props {
  className?: string
  /** Center clip color; defaults to the brand emerald. */
  clipColor?: string
}

export function BrandMark({ className, clipColor = "#10B981" }: Props) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" aria-hidden="true" role="img">
      {/* layer B — the cut behind */}
      <g stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" opacity="0.45">
        <path d="M16.5 2.9 H18.8 Q21.1 2.9 21.1 5.2 V7.5" />
        <path d="M7.5 21.1 H5.2 Q2.9 21.1 2.9 18.8 V16.5" />
      </g>
      {/* layer A — the active cut */}
      <g stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
        <path d="M2.9 7.5 V5.2 Q2.9 2.9 5.2 2.9 H7.5" />
        <path d="M16.5 21.1 H18.8 Q21.1 21.1 21.1 18.8 V16.5" />
      </g>
      {/* the assembled clip */}
      <rect x="7.5" y="8.5" width="9" height="7" rx="1.4" fill={clipColor} />
    </svg>
  )
}
