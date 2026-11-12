/**
 * Boot splash — shown once per browser session, ~2s, then fades out.
 * Sequence: the two cut layers intercut (stagger) -> the clip assembles
 * with a pop -> the wordmark lands letter by letter, like frames on a
 * strip -> the tagline types in with a blinking cursor -> the slate
 * line "take 01 · picture locked" (real post-production jargon) closes.
 * Decorative only: aria-hidden, no focusable content.
 */
const WORD = "montaz".split("")

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
        <rect className="splash-clip" x="7.5" y="8.5" width="9" height="7" rx="1.4" fill="#10B981" />
      </svg>

      <div className="text-center">
        <p
          className="text-2xl leading-none font-semibold tracking-tight lowercase text-foreground"
          aria-label="montaz"
        >
          {WORD.map((letter, i) => (
            <span
              key={i}
              className="splash-letter inline-block"
              style={{ animationDelay: `${0.5 + i * 0.07}s` }}
            >
              {letter}
            </span>
          ))}
        </p>
        <p className="mt-2 text-xs tracking-wide text-muted-foreground">
          <span className="splash-tagline">many cuts, one story</span>
          <span className="splash-cursor" />
        </p>
        <p className="splash-slate timecode mt-3">take 01 · picture locked</p>
      </div>
    </div>
  )
}
