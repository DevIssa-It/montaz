/**
 * Boot splash — shown once per browser session, max ~1.5s.
 * The mark's two cut layers fade in staggered (many cuts), then the
 * clip assembles at the center and the wordmark lands — one story.
 * Decorative only: aria-hidden, no focusable content.
 */
export function SplashScreen({ fading }: { fading: boolean }) {
  return (
    <div
      aria-hidden="true"
      className={`fixed inset-0 z-50 flex flex-col items-center justify-center gap-6 bg-background transition-opacity duration-400 ${
        fading ? "opacity-0" : "opacity-100"
      }`}
    >
      <svg viewBox="0 0 24 24" className="h-16 w-16" fill="none">
        <g
          className="splash-layer-b"
          stroke="#EDEDED"
          strokeWidth="1.8"
          strokeLinecap="round"
          opacity="0.45"
        >
          <path d="M16.5 2.9 H18.8 Q21.1 2.9 21.1 5.2 V7.5" />
          <path d="M7.5 21.1 H5.2 Q2.9 21.1 2.9 18.8 V16.5" />
        </g>
        <g className="splash-layer-a" stroke="#EDEDED" strokeWidth="1.8" strokeLinecap="round">
          <path d="M2.9 7.5 V5.2 Q2.9 2.9 5.2 2.9 H7.5" />
          <path d="M16.5 21.1 H18.8 Q21.1 21.1 21.1 18.8 V16.5" />
        </g>
        <circle className="splash-dot" cx="12" cy="12" r="2.7" fill="#10B981" />
      </svg>
      <div className="splash-word text-center">
        <p className="text-2xl font-semibold tracking-tight lowercase text-foreground">montaz</p>
        <p className="mt-1 text-xs tracking-wide text-muted-foreground">many cuts, one story</p>
      </div>
    </div>
  )
}
