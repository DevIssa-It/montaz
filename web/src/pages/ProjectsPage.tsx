import { useEffect, useRef, useState } from "react"
import { toast } from "sonner"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
} from "@/components/ui/card"
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
  projects: Project[] | null // SSOT: owned by App, not fetched here
  onRefresh: () => void
  activeProjectId: string | null
  onOpenStudio: (id: string) => void
  onOpenRender: (id: string) => void
}

export function ProjectsPage({ projects, onRefresh, activeProjectId, onOpenStudio, onOpenRender }: Props) {
  const [settings, setSettings] = useState<Settings | null>(null)
  const [name, setName] = useState("")
  const [folder, setFolder] = useState("")
  const [appUrl, setAppUrl] = useState("")
  const [creating, setCreating] = useState(false)
  const [picking, setPicking] = useState(false)
  const [polish, setPolish] = useState(false)
  const pickAbort = useRef<AbortController | null>(null)
  const [genBusy, setGenBusy] = useState<string | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<Project | null>(null)

  useEffect(() => {
    void api.getSettings().then(setSettings).catch(() => {})
  }, [])

  const aiReady = !!(settings?.api_keys?.openai || settings?.api_keys?.gemini)

  // Native OS folder picker (opened by the local server, returns an absolute path)
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

  // Quick-fill chips: folders the user used before (derived from existing projects)
  const recentFolders = [
    ...new Set((projects ?? []).map((p) => p.project_folder).filter(Boolean)),
  ]

  const refresh = () => {
    onRefresh()
  }

  const create = async () => {
    if (!name.trim()) return
    setCreating(true)
    try {
      await api.createProject(name.trim(), folder.trim(), appUrl.trim())
      setName("")
      setFolder("")
      setAppUrl("")
      toast.success("Project created.")
      refresh()
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
      refresh()
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
      refresh()
    } catch (err) {
      toast.error((err as Error).message)
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Projects</h1>
        <p className="text-sm text-muted-foreground">
          Point the studio at your project folder and the URL where your web app is running, then
          generate the script.
        </p>
      </div>

      {/* Create */}
      <Card>
        <CardContent className="space-y-4 p-5">
          <div className="border-b border-border/60 pb-3">
            <span className="text-xs font-medium tracking-wider text-muted-foreground uppercase">
              New project
            </span>
          </div>
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
                  <Label htmlFor="p-folder">Project folder (local path)</Label>
                  <div className="flex items-center gap-1.5">
                    {picking && (
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-7"
                        onClick={() => pickAbort.current?.abort()}
                      >
                        Cancel picker
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-7"
                      disabled={picking}
                      onClick={() => void browseFolder()}
                    >
                      {picking ? "Pick a folder in the dialog…" : "Browse…"}
                    </Button>
                  </div>
                </div>
                <Input
                  id="p-folder"
                  placeholder="paste a path here, or click Browse…"
                  value={folder}
                  onChange={(e) => setFolder(e.target.value)}
                />
                {recentFolders.length > 0 && !folder && (
                  <div className="flex flex-wrap gap-1.5">
                    <span className="timecode leading-6">recent:</span>
                    {recentFolders.map((f) => (
                      <button
                        key={f}
                        type="button"
                        onClick={() => setFolder(f)}
                        title={f}
                        className="rounded-sm border border-border px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground transition-colors hover:border-input hover:text-foreground"
                      >
                        {f.split("/").pop()}
                      </button>
                    ))}
                  </div>
                )}
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
          </div>
          <div className="flex justify-end">
            <Button onClick={() => void create()} disabled={creating || !name.trim()}>
              {creating ? "Creating…" : "Create project"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* AI polish toggle — one global switch for all generate actions */}
      {projects !== null && projects.length > 0 && (
        <div className="flex items-center gap-3 rounded-md border border-border bg-card px-4 py-3">
          <Switch
            id="polish"
            checked={polish}
            disabled={!aiReady}
            onCheckedChange={(v) => setPolish(v)}
          />
          <label htmlFor="polish" className="text-sm">
            Polish narration with AI
          </label>
          {aiReady ? (
            <span className="timecode ml-auto">openai / gemini</span>
          ) : (
            <span className="text-xs text-muted-foreground">
              needs an OpenAI or Gemini key — Settings
            </span>
          )}
        </div>
      )}

      {/* List */}
      <div className="space-y-2">
        <span className="text-xs font-medium tracking-wider text-muted-foreground uppercase">
          {projects === null ? "Loading…" : `Your projects (${projects.length})`}
        </span>
        {projects === null ? (
          <Skeleton className="h-24 w-full" />
        ) : projects.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center text-sm text-muted-foreground">
              No projects yet — create the first one above.
            </CardContent>
          </Card>
        ) : (
          projects.map((p) => (
            <Card
              key={p.id}
              className={p.id === activeProjectId ? "border-primary/50" : undefined}
            >
              <CardContent className="flex flex-wrap items-center gap-3 p-4">
                <div className="min-w-48 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold">{p.name}</span>
                    <Badge variant="outline" className="font-mono text-[10px]">
                      {p.scenes.length} scenes
                    </Badge>
                  </div>
                  <p className="mt-1 truncate font-mono text-xs text-muted-foreground">
                    {p.project_folder || "no folder set"}
                  </p>
                  <p className="truncate font-mono text-xs text-muted-foreground">
                    {p.app_url || "no app URL set"}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    onClick={() => void generate(p)}
                    disabled={genBusy === p.id || !p.project_folder}
                  >
                    {genBusy === p.id ? "Generating…" : p.scenes.length ? "Regenerate script" : "Generate script"}
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => onOpenStudio(p.id)}>
                    Studio
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onOpenRender(p.id)}
                    disabled={p.scenes.length === 0}
                  >
                    Render
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="text-destructive"
                    onClick={() => setDeleteTarget(p)}
                  >
                    Delete
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

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
