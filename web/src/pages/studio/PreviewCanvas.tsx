import type { Scene } from "@/types"

/** 16:9 letterbox mockup of what the renderer will produce for this scene. */
export function PreviewCanvas({ scene, appUrl }: { scene: Scene; appUrl: string }) {
  const v = scene.visual
  return (
    <div className="aspect-video w-full max-w-xl overflow-hidden rounded-md border border-border bg-[#090A0F]">
      {v.type === "card" && (
        <div className="flex h-full flex-col justify-center px-10">
          <div className="mb-4 h-1 w-12 bg-primary" />
          <p className="text-2xl font-semibold tracking-tight">{v.card?.heading || scene.title || "Untitled"}</p>
          {v.card?.kind !== "title" && v.card?.bullets.length ? (
            <ul className="mt-4 space-y-1.5">
              {v.card.bullets.slice(0, 5).map((b, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                  {b}
                </li>
              ))}
            </ul>
          ) : (
            v.card?.bullets[0] && (
              <p className="mt-3 text-sm text-muted-foreground">{v.card.bullets[0]}</p>
            )
          )}
        </div>
      )}

      {v.type === "browser" && (
        <div className="flex h-full flex-col p-5">
          <div className="flex items-center gap-2 rounded-md border border-border bg-card px-3 py-1.5">
            <span className="rec-dot" />
            <span className="truncate font-mono text-xs text-muted-foreground">
              {appUrl || "app URL not set"}
            </span>
            <span className="timecode ml-auto">playwright</span>
          </div>
          <div className="mt-3 flex-1 overflow-hidden rounded-md border border-border bg-card">
            <table className="w-full font-mono text-xs">
              <tbody>
                {(v.actions ?? []).map((a, i) => (
                  <tr key={i} className="border-b border-border/60 last:border-0">
                    <td className="w-8 px-2 py-1.5 text-right text-muted-foreground">{i + 1}</td>
                    <td className="px-2 py-1.5 text-primary">{a.do}</td>
                    <td className="truncate px-2 py-1.5 text-muted-foreground">
                      {a.url ?? a.selector ?? a.text ?? a.key ?? (a.ms ? `${a.ms}ms` : a.seconds ? `${a.seconds}s` : "")}
                    </td>
                  </tr>
                ))}
                {(v.actions ?? []).length === 0 && (
                  <tr>
                    <td colSpan={3} className="px-2 py-3 text-center text-muted-foreground">
                      no capture steps yet
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {v.type === "terminal" && (
        <div className="flex h-full flex-col p-5">
          <div className="flex-1 rounded-md border border-border bg-[#0A0D14] p-4 font-mono text-xs">
            <p className="text-foreground">$ {v.command || "npm run demo"}</p>
            <p className="mt-2 text-muted-foreground">output is captured live at render time…</p>
          </div>
        </div>
      )}

      {(v.type === "image" || v.type === "video") && (
        <div className="flex h-full items-center justify-center p-5">
          {v.path ? (
            v.type === "image" ? (
              <img src={`/api/data/${v.path}`} alt={scene.title} className="max-h-full max-w-full object-contain" />
            ) : (
              <video src={`/api/data/${v.path}`} className="max-h-full max-w-full" controls muted />
            )
          ) : (
            <p className="text-xs text-muted-foreground">no asset yet — upload one in the inspector</p>
          )}
        </div>
      )}
    </div>
  )
}
