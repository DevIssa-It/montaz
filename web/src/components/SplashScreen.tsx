/**
 * Boot splash — shown once per browser session, ~2s, then fades out.
 * Sequence: cut B slides in, cut A intercuts over it, then the story
 * (the intersection of both cuts) assembles with a pop — many cuts,
 * one story — wordmark letter by letter, typewriter tagline with a
 * blinking cursor, closing slate "take 01 · picture locked".
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
        <defs>
          <clipPath id="splash-cutA">
            <rect x="5" y="5" width="10" height="10" rx="2" />
          </clipPath>
        </defs>
        <rect
          className="splash-layer-b"
          x="9"
          y="9"
          width="10"
          height="10"
          rx="2"
          stroke="#EDEDED"
          strokeWidth="1.8"
          opacity="0.45"
        />
        <rect
          className="splash-layer-a"
          x="5"
          y="5"
          width="10"
          height="10"
          rx="2"
          stroke="#EDEDED"
          strokeWidth="1.8"
        />
        <rect
          className="splash-clip"
          x="9"
          y="9"
          width="10"
          height="10"
          rx="2"
          fill="#FBBF24"
          clip-path="url(#splash-cutA)"
        />
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
