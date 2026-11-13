import { useEffect, useRef, useState } from "react"
import { toast } from "sonner"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { api } from "@/lib/api"
import type { Project, RenderStatusInfo } from "@/types"

/**
 * Render lives inside the editor — pipeline-first, one click, no page switch.
 * Slim strip: button + inline progress; done -> link to the final MP4.
 */
export function RenderStrip({ project, onProjectUpdated }: { project: Project; onProjectUpdated: (p: Project) => void }) {
  const [status, setStatus] = useState<RenderStatusInfo>({ state: "idle", progress: 0, message: "" })
  const [starting, setStarting] = useState(false)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
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
  }, [project.id, onProjectUpdated])

  const start = async () => {
    setStarting(true)
    try {
      await api.render(project.id)
      toast.info("Render started — narrating, capturing, and assembling.")
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setStarting(false)
    }
  }

  const running = status.state === "running"
  const scenesWithAudio = project.scenes.filter((s) => s.audio).length

  return (
    <div className="border-t border-border bg-card px-4 py-2">
      <div className="flex items-center gap-3">
        <Button size="sm" onClick={() => void start()} disabled={running || starting || project.scenes.length === 0}>
          {running ? "Rendering…" : starting ? "Starting…" : "Render video"}
        </Button>
        {running && <span className="rec-dot" />}
        <Badge variant="outline" className="timecode">
          {scenesWithAudio}/{project.scenes.length} audio
        </Badge>
        <span className="timecode hidden truncate sm:inline">{status.message}</span>
        <div className="ml-auto flex items-center gap-3">
          {running && <Progress value={Math.round(status.progress * 100)} className="w-40" />}
          {status.state === "done" && status.output && (
            <>
              <Badge className="bg-primary/15 text-primary">done</Badge>
              <a
                href={status.output}
                target="_blank"
                rel="noreferrer"
                className="text-sm text-primary underline-offset-4 hover:underline"
              >
                Open MP4
              </a>
            </>
          )}
          {status.state === "error" && (
            <p className="max-w-72 truncate text-xs text-destructive">{status.error}</p>
          )}
        </div>
      </div>
      {status.error && <p className="mt-1 text-xs text-destructive">{status.error}</p>}
      {running && (status.steps ?? []).length > 0 && (
        <p className="timecode mt-1 truncate">latest: {(status.steps ?? []).slice(-1)[0]}</p>
      )}
    </div>
  )
}
