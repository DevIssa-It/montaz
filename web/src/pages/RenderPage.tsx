import { useEffect, useRef, useState } from "react"
import { toast } from "sonner"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
import { api } from "@/lib/api"
import type { Project, RenderStatusInfo } from "@/types"

interface Props {
  project: Project | null
  onProjectUpdated: (p: Project) => void
}

export function RenderPage({ project, onProjectUpdated }: Props) {
  const [status, setStatus] = useState<RenderStatusInfo>({ state: "idle", progress: 0, message: "" })
  const [bgmEnabled, setBgmEnabled] = useState(project?.bgm.enabled ?? false)
  const [bgmVolume, setBgmVolume] = useState(project?.bgm.volume ?? 0.15)
  const [starting, setStarting] = useState(false)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // SSOT note: render status is server-owned; we only poll and display it.
  useEffect(() => {
    if (!project) return
    const poll = () => {
      void api
        .renderStatus(project.id)
        .then((s) => {
          setStatus(s)
          if (s.state === "done") {
            clearInterval(timerRef.current ?? undefined)
            void api.getProject(project.id).then(onProjectUpdated)
          }
        })
        .catch(() => clearInterval(timerRef.current ?? undefined))
    }
    poll()
    timerRef.current = setInterval(poll, 1500)
    return () => clearInterval(timerRef.current ?? undefined)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [project?.id])

  if (!project) {
    return (
      <div className="p-6">
        <Card>
          <CardContent className="p-10 text-center text-sm text-muted-foreground">
            No project selected. Pick one on the Projects page first.
          </CardContent>
        </Card>
      </div>
    )
  }

  const start = async () => {
    setStarting(true)
    try {
      // Persist BGM choice before rendering so the pipeline sees it.
      const updated = await api.updateProject(project.id, {
        bgm: { enabled: bgmEnabled, path: project.bgm.path, volume: bgmVolume },
      })
      onProjectUpdated(updated)
      await api.render(project.id)
      toast.info("Render started — narrating, capturing, and assembling.")
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setStarting(false)
    }
  }

  const scenesWithAudio = project.scenes.filter((s) => s.audio).length
  const running = status.state === "running"

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Render</h1>
        <p className="text-sm text-muted-foreground">
          One click: TTS narration → headless capture / cards → crossfade assembly → MP4.
        </p>
      </div>

      <Card>
        <CardContent className="space-y-4 p-5">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <span className="text-sm font-semibold">{project.name}</span>
            <Badge variant="outline" className="font-mono text-[10px]">
              {scenesWithAudio}/{project.scenes.length} scenes have audio
            </Badge>
          </div>

          {project.scenes.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No scenes yet — generate the script on the Projects page first.
            </p>
          ) : scenesWithAudio === 0 ? (
            <p className="text-sm text-muted-foreground">
              Narration audio is synthesized automatically during the render.
            </p>
          ) : null}

          {/* BGM options */}
          <div className="flex items-center gap-3">
            <Switch id="bgm" checked={bgmEnabled} onCheckedChange={(v) => setBgmEnabled(v)} />
            <label htmlFor="bgm" className="text-sm">
              Background music (optional, needs <code className="font-mono text-xs">bgm.path</code> set)
            </label>
            {bgmEnabled && (
              <div className="ml-auto flex items-center gap-2">
                <Slider
                  className="w-32"
                  value={[bgmVolume]}
                  min={0}
                  max={0.5}
                  step={0.05}
                  onValueChange={(vals) => setBgmVolume(Array.isArray(vals) ? vals[0] : vals)}
                />
                <span className="timecode w-9">{bgmVolume.toFixed(2)}</span>
              </div>
            )}
          </div>

          <div className="flex items-center gap-3">
            <Button onClick={() => void start()} disabled={running || starting || project.scenes.length === 0}>
              {running ? "Rendering…" : starting ? "Starting…" : "Render video"}
            </Button>
            {running && <span className="rec-dot" />}
          </div>

          {/* Progress + steps */}
          {status.state !== "idle" && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm">{status.message}</span>
                <span className="timecode">{Math.round(status.progress * 100)}%</span>
              </div>
              <Progress value={Math.round(status.progress * 100)} />
              {status.error ? (
                <p className="text-sm text-destructive">{status.error}</p>
              ) : (
                (status.steps ?? []).length > 0 && (
                  <div className="max-h-40 overflow-auto rounded-md border border-border bg-card p-2 font-mono text-xs text-muted-foreground">
                    {(status.steps ?? []).map((s, i) => (
                      <p key={i}>{s}</p>
                    ))}
                  </div>
                )
              )}
            </div>
          )}

          {/* Result */}
          {status.state === "done" && status.output && (
            <div className="space-y-2 border-t border-border/60 pt-4">
              <div className="flex items-center gap-2">
                <Badge className="bg-primary/15 text-primary">done</Badge>
                <a href={status.output} download className="text-sm text-primary underline-offset-4 hover:underline">
                  Download MP4
                </a>
              </div>
              <video src={status.output} controls className="w-full rounded-md border border-border" />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
