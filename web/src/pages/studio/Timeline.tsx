import { useMemo, useState } from "react"

import type { Scene } from "@/types"

const PX_PER_SEC = 56
const MIN_W = 64

interface Props {
  projectId: string
  scenes: Scene[]
  durations: Record<string, number>
  selectedId: string | null
  onSelect: (id: string) => void
  onReorder: (from: number, insertBefore: number) => void
  bgmEnabled: boolean
}

type DragState = { from: number; over: number; side: "left" | "right" } | null

/**
 * Review timeline — a lightweight arrange surface, NOT an editing tool:
 * each scene block is as wide as its narration duration; drag blocks to
 * reorder. The pipeline (scriptgen -> capture -> render) does the rest.
 */
export function Timeline({ projectId, scenes, durations, selectedId, onSelect, onReorder, bgmEnabled }: Props) {
  const [drag, setDrag] = useState<DragState>(null)

  const widths = useMemo(
    () =>
      scenes.map((s) => {
        const d = durations[s.id] ?? estimateSeconds(s)
        return Math.max(MIN_W, Math.round(d * PX_PER_SEC))
      }),
    [scenes, durations]
  )
  const total = useMemo(() => widths.reduce((a, b) => a + b, 0), [widths])

  const handleDrop = (overIndex: number, side: "left" | "right") => {
    if (drag?.from === undefined) return
    const insertBefore = side === "left" ? overIndex : overIndex + 1
    onReorder(drag.from, insertBefore)
    setDrag(null)
  }

  const totalSeconds = useMemo(() => {
    const seconds = scenes.reduce((acc, s) => acc + (durations[s.id] ?? estimateSeconds(s)), 0)
    return `${Math.round(seconds)}s`
  }, [scenes, durations])

  return (
    <div className="rounded-md border border-border bg-card">
      <div className="flex items-center gap-2 border-b border-border/60 px-3 py-1.5">
        <span className="text-[10px] font-medium tracking-wider text-muted-foreground uppercase">
          Timeline
        </span>
        <span className="timecode">drag to reorder · review layer</span>
        <span className="timecode ml-auto">
          total ≈ {totalSeconds}
        </span>
      </div>

      <div className="overflow-x-auto p-2">
        {/* scene track */}
        <div className="flex min-h-14 items-stretch gap-px">
          {scenes.map((scene, i) => {
            const w = widths[i]
            const isDragging = drag?.from === i
            const dropLeft = drag && drag.over === i && drag.side === "left" && drag.from !== i
            const dropRight = drag && drag.over === i && drag.side === "right" && drag.from !== i
            return (
              <div
                key={scene.id}
                role="button"
                tabIndex={0}
                draggable
                onDragStart={(e) => {
                  e.dataTransfer.setData("text/plain", String(i))
                  e.dataTransfer.effectAllowed = "move"
                  setDrag({ from: i, over: i, side: "left" })
                }}
                onDragOver={(e) => {
                  e.preventDefault()
                  const rect = e.currentTarget.getBoundingClientRect()
                  const side = e.clientX < rect.left + rect.width / 2 ? "left" : "right"
                  if (drag?.from !== undefined && drag.from !== i) setDrag({ from: drag.from, over: i, side })
                }}
                onDrop={(e) => {
                  e.preventDefault()
                  handleDrop(i, drag?.side ?? "left")
                }}
                onDragEnd={() => setDrag(null)}
                onClick={() => onSelect(scene.id)}
                onKeyDown={(e) => e.key === "Enter" && onSelect(scene.id)}
                title={scene.title}
                style={{ width: w }}
                className={`group relative cursor-grab overflow-hidden rounded-md border transition-colors active:cursor-grabbing ${
                  scene.id === selectedId
                    ? "border-primary"
                    : "border-border hover:border-input"
                } ${dropLeft ? "border-l-2 border-l-primary" : ""} ${dropRight ? "border-r-2 border-r-primary" : ""} ${
                  isDragging ? "opacity-40" : ""
                }`}
              >
                {/* real frame from the server (card render / browser shot / video frame) */}
                <img
                  src={`/api/projects/${projectId}/thumbs/${scene.id}.png`}
                  alt=""
                  loading="lazy"
                  className="absolute inset-0 h-full w-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/25 to-black/5" />
                <div className="relative flex h-14 flex-col justify-end px-2 py-1">
                  <p className="truncate text-[11px] font-medium text-foreground">
                    <span className="timecode mr-1">{String(i + 1).padStart(2, "0")}</span>
                    {scene.title || "Untitled"}
                  </p>
                  <p className="timecode mt-0.5">
                    {scene.visual.type} · {(durations[scene.id] ?? estimateSeconds(scene)).toFixed(1)}s
                  </p>
                </div>
              </div>
            )
          })}
          {scenes.length === 0 && (
            <p className="timecode px-2 py-2">no scenes yet</p>
          )}
        </div>

        {/* narration track */}
        <div className="mt-1 flex items-stretch gap-px">
          {scenes.map((scene, i) => (
            <div key={scene.id} style={{ width: widths[i] }} className="px-px">
              <div
                className={`flex h-3 items-center rounded-sm ${
                  scene.audio ? "bg-primary/30" : "border border-dashed border-border/60"
                }`}
                title={scene.audio ? "narration audio ready" : "no narration audio yet"}
              >
                {scene.audio && <span className="timecode px-1 text-[9px]">♪</span>}
              </div>
            </div>
          ))}
          {scenes.length === 0 && <div className="h-3" />}
        </div>

        {/* bgm track */}
        {bgmEnabled && (
          <div className="mt-1">
            <div
              style={{ width: Math.max(total, MIN_W) }}
              className="flex h-3 items-center rounded-sm bg-primary/15"
            >
              <span className="timecode px-1 text-[9px]">BGM</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function estimateSeconds(scene: Scene): number {
  const words = scene.narration.trim().split(/\s+/).filter(Boolean).length
  return Math.max(words / 2.5, 1.5) // ~150 wpm narration
}
