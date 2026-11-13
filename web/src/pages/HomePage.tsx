import { useEffect, useRef, useState } from "react"
import { toast } from "sonner"

import { BrandMark } from "@/components/BrandMark"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { Switch } from "@/components/ui/switch"
import { api } from "@/lib/api"
import type { Project, Settings } from "@/types"

interface Props {
  projects: Project[] | null
  onRefresh: () => void
  activeProjectId: string | null
  onOpenStudio: (id: string) => void
}

const STEPS = [
  {
    n: "01",
    title: "Point at your project",
    body: "Pick the folder of the app you are building — montaz reads its README, stack, and routes.",
  },
  {
    n: "02",
    title: "Generate & review the script",
    body: "A narration script appears scene by scene. Edit any line, then let TTS voice it.",
  },
  {
    n: "03",
    title: "Render the demo film",
    body: "montaz captures your running app headlessly, voices the narration, and assembles the MP4.",
  },
]

function timeAgo(ts?: number): string {
  if (!ts) return "—"
  const diff = Date.now() / 1000 - ts
  if (diff < 3600) return `${Math.max(1, Math.round(diff / 60))} min ago`
  if (diff < 86400) return `${Math.round(diff / 3600)} h ago`
  return `${Math.round(diff / 86400)} d ago`
}

export function HomePage({ projects, onRefresh, onOpenStudio }: Props) {
  const [settings, setSettings] = useState<Settings | null>(null)
  const [creating, setCreating] = useState(false)
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState("")
  const [folder, setFolder] = useState("")
  const [appUrl, setAppUrl] = useState("")
  const [picking, setPicking] = useState(false)
  const pickAbort = useRef<AbortController | null>(null)
  const [polish, setPolish] = useState(false)
  const [genBusy, setGenBusy] = useState<string | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<Project | null>(null)

  useEffect(() => {
    void api.getSettings().then(setSettings).catch(() => {})
  }, [])

  const aiReady = !!(settings?.api_keys?.openai || settings?.api_keys?.gemini)

  const browseFolder = async () => {
    setPicking(true)
    pickAbort.current = new AbortController()
    try {
      const resp = await fetch("/api/system/pick-folder", {
        method: "POST",
        signal: pickAbort.current.signal,
      })
      if (!resp.ok) throw new Error((await resp.json()).detail ?? `HTTP ${resp.status}`)
      const data = await resp.json()
      if (data.path) setFolder(String(data.path).replace(/\\/g, "/"))
    } catch (err) {
      if ((err as Error).name !== "AbortError") toast.error((err as Error).message)
    } finally {
      setPicking(false)
      pickAbort.current = null
    }
  }

  const create = async () => {
    if (!name.trim()) return
    setCreating(true)
    try {
      const created = await api.createProject(name.trim(), folder.trim(), appUrl.trim())
      toast.success("Project created.")
      setName("")
      setFolder("")
      setAppUrl("")
      setShowCreate(false)
      onRefresh()
      if (created.project_folder) void generate(created) // pipeline-first: script right away
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setCreating(false)
    }
  }

  const generate = async (project: Project) => {
    setGenBusy(project.id)
    try {
      const language = settings?.language ?? "en-US"
      const updated = await api.scriptgen(project.id, language, polish)
      toast.success(`Script generated — ${updated.scenes.length} scenes.`)
      onRefresh()
      onOpenStudio(project.id)
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setGenBusy(null)
    }
  }

  const remove = async () => {
    if (!deleteTarget) return
    try {
      await api.deleteProject(deleteTarget.id)
      toast.success("Project deleted.")
      setDeleteTarget(null)
      onRefresh()
    } catch (err) {
      toast.error((err as Error).message)
    }
  }

  const createForm = (
    <div className="grid gap-4">
      <div className="space-y-2">
        <Label htmlFor="p-name">Project name</Label>
        <Input
          id="p-name"
          placeholder="e.g. KostFinder"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="p-folder">Project folder</Label>
            <Button
              size="sm"
              variant="outline"
              className="h-7"
              disabled={picking}
              onClick={() => void browseFolder()}
            >
              {picking ? "Pick in the dialog…" : "Browse…"}
            </Button>
          </div>
          <Input
            id="p-folder"
            placeholder="paste a path here, or click Browse…"
            value={folder}
            onChange={(e) => setFolder(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="p-url">Web app URL (running)</Label>
          <Input
            id="p-url"
            placeholder="http://localhost:3000"
            value={appUrl}
            onChange={(e) => setAppUrl(e.target.value)}
          />
        </div>
      </div>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Switch id="polish" checked={polish} disabled={!aiReady} onCheckedChange={(v) => setPolish(v)} />
          <Label htmlFor="polish">Polish narration with AI</Label>
          {!aiReady && <span className="text-xs text-muted-foreground">needs an OpenAI or Gemini key</span>}
        </div>
        <Button onClick={() => void create()} disabled={creating || !name.trim()}>
          {creating ? "Creating…" : "Create project"}
        </Button>
      </div>
    </div>
  )

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Projects</h1>
          <p className="text-sm text-muted-foreground">
            Every demo film you have built with montaz.
          </p>
        </div>
        <Button onClick={() => setShowCreate((v) => !v)} aria-expanded={showCreate}>
          {showCreate ? "Close" : "+ New project"}
        </Button>
      </div>

      {/* create form — collapsed by default, open when empty or on demand */}
      {(showCreate || (projects !== null && projects.length === 0)) && (
        <Card>
          <CardContent className="space-y-4 p-5">
            <div className="border-b border-border/60 pb-3">
              <span className="text-xs font-medium tracking-wider text-muted-foreground uppercase">
                New project
              </span>
            </div>
            {createForm}
          </CardContent>
        </Card>
      )}

      {/* Onboarding empty state */}
      {projects === null ? (
        <div className="grid gap-4 sm:grid-cols-3">
          <Skeleton className="h-44" />
          <Skeleton className="h-44" />
          <Skeleton className="h-44" />
        </div>
      ) : projects.length === 0 ? (
        <div className="rounded-md border border-border bg-card p-8">
          <div className="mb-6 flex items-center gap-2">
            <BrandMark className="h-6 w-6 text-foreground" />
            <span className="text-sm font-semibold lowercase">montaz</span>
            <span className="timecode">three steps to your demo film</span>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            {STEPS.map((s) => (
              <div key={s.n} className="rounded-md border border-border bg-background p-4">
                <p className="timecode mb-2">{s.n}</p>
                <p className="text-sm font-semibold">{s.title}</p>
                <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{s.body}</p>
              </div>
            ))}
          </div>
          <p className="mt-6 text-xs text-muted-foreground">
            Fill the form above with your project folder and the URL where it is running — the
            pipeline handles the rest.
          </p>
        </div>
      ) : (
        /* Project gallery */
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((p) => {
            const firstScene = p.scenes[0]
            const thumb = firstScene ? `/api/projects/${p.id}/thumbs/${firstScene.id}.png` : null
            return (
              <Card key={p.id} className="overflow-hidden">
                <button
                  type="button"
                  onClick={() => onOpenStudio(p.id)}
                  className="block w-full text-left focus-visible:outline-2 focus-visible:outline-ring"
                  title={`Open ${p.name} in the studio`}
                >
                  <div className="relative aspect-video w-full overflow-hidden border-b border-border bg-[#090A0F]">
                    {thumb ? (
                      <img
                        src={thumb}
                        alt=""
                        loading="lazy"
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <div className="flex h-full items-center justify-center">
                        <BrandMark className="h-8 w-8 text-muted-foreground" />
                      </div>
                    )}
                    <Badge
                      className={`absolute right-2 top-2 ${
                        p.rendered ? "bg-primary/90 text-primary-foreground" : "bg-card/90 text-muted-foreground"
                      }`}
                      variant="secondary"
                    >
                      {p.rendered ? "rendered" : `${p.scenes.length} scenes`}
                    </Badge>
                  </div>
                </button>
                <CardContent className="space-y-2 p-4">
                  <div className="flex items-start justify-between gap-2">
                    <button
                      type="button"
                      onClick={() => onOpenStudio(p.id)}
                      className="truncate text-sm font-semibold hover:underline focus-visible:outline-2 focus-visible:outline-ring"
                      title={p.name}
                    >
                      {p.name}
                    </button>
                    <Badge variant="outline" className="timecode shrink-0">
                      {p.scenes.length} scenes
                    </Badge>
                  </div>
                  <p className="timecode">
                    {timeAgo((p as Project & { updated_at?: number }).updated_at)}
                  </p>
                  <div className="flex flex-wrap gap-2 pt-1">
                    <Button size="sm" onClick={() => onOpenStudio(p.id)}>
                      Open
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => void generate(p)}
                      disabled={genBusy === p.id || !p.project_folder}
                    >
                      {genBusy === p.id ? "Generating…" : "Regenerate script"}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="ml-auto text-destructive"
                      onClick={() => setDeleteTarget(p)}
                    >
                      Delete
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {/* Delete confirm */}
      <Dialog open={deleteTarget !== null} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete “{deleteTarget?.name}”?</DialogTitle>
            <DialogDescription>
              This permanently removes its scenes, audio, and rendered video from this machine.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={() => void remove()}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
