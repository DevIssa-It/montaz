/**
 * Montaz mark — many cuts, one story.
 * Two intercut frames; the emerald shape is their intersection: the
 * story exists where the cuts overlap. Layer B (dimmed) sits behind
 * layer A (full), their common region carries the accent.
 * Pure geometry — no gradients, no glow.
 */
import { useId } from "react"

interface Props {
  className?: string
  /** Intersection color; defaults to the brand gold. */
  storyColor?: string
}

export function BrandMark({ className, storyColor = "#FBBF24" }: Props) {
  const clipId = useId()
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" aria-hidden="true" role="img">
      <defs>
        <clipPath id={clipId}>
          <rect x="5" y="5" width="10" height="10" rx="2" />
        </clipPath>
      </defs>
      {/* cut B — behind */}
      <rect x="9" y="9" width="10" height="10" rx="2" stroke="currentColor" strokeWidth="1.8" opacity="0.45" />
      {/* cut A — on top */}
      <rect x="5" y="5" width="10" height="10" rx="2" stroke="currentColor" strokeWidth="1.8" />
      {/* the story: where the two cuts meet */}
      <rect
        x="9"
        y="9"
        width="10"
        height="10"
        rx="2"
        fill={storyColor}
        clipPath={`url(#${clipId})`}
      />
    </svg>
  )
}
