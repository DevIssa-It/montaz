import { useEffect, useMemo, useRef, useState } from "react"
import { toast } from "sonner"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { Textarea } from "@/components/ui/textarea"
import { api, visualLabel } from "@/lib/api"
import type { CardKind, CaptureAction, Project, Scene, VisualType } from "@/types"

const VISUAL_TYPES: VisualType[] = ["card", "browser", "terminal", "image", "video"]
const ACTION_KINDS = ["goto", "click", "fill", "press", "scroll", "wait", "record"] as const

const EMPTY_ACTION: CaptureAction = { do: "wait", ms: 500 }

function newSceneDraft(index: number): Scene {
  return {
    id: `sc_${Math.random().toString(16).slice(2, 10)}`,
    title: `Scene ${index + 1}`,
    narration: "",
    visual: { type: "card", card: { kind: "title", heading: "", bullets: [] } },
    audio: null,
  }
}

interface Props {
  project: Project | null
  onProjectUpdated: (p: Project) => void
}

export function StudioPage({ project, onProjectUpdated }: Props) {
  const [scenes, setScenes] = useState<Scene[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [dirty, setDirty] = useState(false)
  const [saving, setSaving] = useState(false)
  const [previewing, setPreviewing] = useState<string | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  useEffect(() => {
    if (project) {
      setScenes(project.scenes)
      setSelectedId(project.scenes[0]?.id ?? null)
      setDirty(false)
    }
  }, [project])

  const selected = useMemo(() => scenes.find((s) => s.id === selectedId) ?? null, [scenes, selectedId])

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

  const mutate = (fn: (draft: Scene[]) => Scene[]) => {
    setScenes((prev) => fn(prev))
    setDirty(true)
  }

  const updateScene = (id: string, patch: Partial<Scene>) =>
    mutate((prev) => prev.map((s) => (s.id === id ? { ...s, ...patch } : s)))

  const saveAll = async () => {
    setSaving(true)
    try {
      const updated = await api.updateProject(project.id, { scenes })
      onProjectUpdated(updated)
      setScenes(updated.scenes)
      setDirty(false)
      toast.success("Scenes saved.")
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setSaving(false)
    }
  }

  const previewAudio = async (scene: Scene) => {
    setPreviewing(scene.id)
    try {
      const result = await api.previewAudio(project.id, scene.id)
      // Bust cache so a re-synthesized narration replays fresh.
      audioRef.current?.setAttribute("src", `${result.audio}?t=${Date.now()}`)
      void audioRef.current?.play()
      const fresh = scenes.map((s) => (s.id === scene.id ? { ...s, audio: result.audio } : s))
      setScenes(fresh)
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setPreviewing(null)
    }
  }

  const uploadAsset = async (scene: Scene, file: File) => {
    try {
      const result = await api.uploadAsset(project.id, file)
      updateScene(scene.id, { visual: { ...scene.visual, type: file.type.startsWith("video") ? "video" : "image", path: result.path } })
      toast.success(`Asset uploaded: ${result.path}`)
    } catch (err) {
      toast.error((err as Error).message)
    }
  }

  return (
    <div className="flex h-[calc(100vh-3.25rem)] flex-col">
      {/* Toolbar */}
      <div className="flex items-center gap-3 border-b border-border px-4 py-2">
        <span className="text-sm font-semibold">{project.name}</span>
        <Badge variant="outline" className="timecode">
          {scenes.length} scenes
        </Badge>
        <span className="rec-dot" title="Captured at render time" />
        <span className="timecode">auto-capture armed</span>
        <div className="ml-auto flex items-center gap-2">
          {dirty && <span className="text-xs text-warning">unsaved changes</span>}
          <Button size="sm" onClick={() => void saveAll()} disabled={saving || !dirty}>
            {saving ? "Saving…" : "Save all"}
          </Button>
        </div>
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-[280px_1fr_340px]">
        {/* Scene list */}
        <div className="min-h-0 border-r border-border">
          <div className="flex items-center justify-between px-3 py-2">
            <span className="text-xs font-medium tracking-wider text-muted-foreground uppercase">Scenes</span>
            <Button
              size="sm"
              variant="outline"
              className="h-7"
              onClick={() => {
                const scene = newSceneDraft(scenes.length)
                mutate((prev) => [...prev, scene])
                setSelectedId(scene.id)
              }}
            >
              + Add
            </Button>
          </div>
          <ScrollArea className="h-[calc(100%-2.5rem)]">
            {scenes.length === 0 ? (
              <p className="px-3 py-8 text-center text-xs text-muted-foreground">
                Empty script — generate one from the Projects page or add scenes manually.
              </p>
            ) : (
              scenes.map((scene, i) => (
                <button
                  key={scene.id}
                  type="button"
                  onClick={() => setSelectedId(scene.id)}
                  className={`w-full border-b border-border/60 px-3 py-2.5 text-left transition-colors hover:bg-accent ${
                    scene.id === selectedId ? "bg-accent" : ""
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="timecode">{String(i + 1).padStart(2, "0")}</span>
                    <span className="truncate text-sm font-medium">
                      {scene.title || "Untitled scene"}
                    </span>
                    {scene.audio && <span className="ml-auto text-xs text-primary">♪</span>}
                  </div>
                  <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-muted-foreground">
                    {scene.narration || "no narration yet"}
                  </p>
                  <Badge variant="outline" className="mt-1.5 text-[10px]">
                    {visualLabel(scene.visual.type)}
                  </Badge>
                </button>
              ))
            )}
          </ScrollArea>
        </div>

        {/* Preview canvas */}
        <div className="flex min-h-0 flex-col items-center justify-center gap-3 bg-background p-6">
          {selected ? (
            <>
              <PreviewCanvas scene={selected} appUrl={project.app_url} />
              <audio ref={audioRef} className="w-full max-w-xl" controls preload="none" />
            </>
          ) : (
            <p className="text-sm text-muted-foreground">Select a scene to preview it.</p>
          )}
        </div>

        {/* Inspector */}
        <div className="min-h-0 border-l border-border">
          <div className="px-3 py-2">
            <span className="text-xs font-medium tracking-wider text-muted-foreground uppercase">
              Inspector
            </span>
          </div>
          <ScrollArea className="h-[calc(100%-2.5rem)]">
            {selected ? (
              <Inspector
                scene={selected}
                project={project}
                onUpdate={(patch) => updateScene(selected.id, patch)}
                onPreviewAudio={() => void previewAudio(selected)}
                onUploadAsset={(file) => void uploadAsset(selected, file)}
                previewing={previewing === selected.id}
                onDelete={() => {
                  mutate((prev) => prev.filter((s) => s.id !== selected.id))
                  setSelectedId(null)
                }}
              />
            ) : (
              <p className="px-3 py-8 text-center text-xs text-muted-foreground">No scene selected.</p>
            )}
          </ScrollArea>
        </div>
      </div>
    </div>
  )
}

/* ------------------------------------------------- preview canvas */

function PreviewCanvas({ scene, appUrl }: { scene: Scene; appUrl: string }) {
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

/* ------------------------------------------------- inspector */

function Inspector({
  scene,
  project,
  onUpdate,
  onPreviewAudio,
  onUploadAsset,
  previewing,
  onDelete,
}: {
  scene: Scene
  project: Project
  onUpdate: (patch: Partial<Scene>) => void
  onPreviewAudio: () => void
  onUploadAsset: (file: File) => void
  previewing: boolean
  onDelete: () => void
}) {
  const v = scene.visual
  return (
    <div className="space-y-4 px-3 py-3">
      <div className="space-y-2">
        <Label htmlFor="insp-title">Scene title</Label>
        <Input
          id="insp-title"
          value={scene.title}
          onChange={(e) => onUpdate({ title: e.target.value })}
        />
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="insp-narration">Narration (spoken)</Label>
          <span className="timecode">{scene.narration.trim().split(/\s+/).filter(Boolean).length} words</span>
        </div>
        <Textarea
          id="insp-narration"
          rows={6}
          value={scene.narration}
          placeholder="What the voice should say in this scene…"
          onChange={(e) => onUpdate({ narration: e.target.value })}
        />
        <Button size="sm" variant="outline" className="w-full" onClick={onPreviewAudio} disabled={previewing || !scene.narration.trim()}>
          {previewing ? "Synthesizing…" : scene.audio ? "Re-synthesize & play" : "Synthesize & play"}
        </Button>
      </div>

      <Separator />

      <div className="space-y-2">
        <Label>Visual type</Label>
        <Select
          value={v.type}
          onValueChange={(t) => {
            const next: VisualType = t as VisualType
            if (next === "card" && !v.card) onUpdate({ visual: { type: next, card: { kind: "title", heading: scene.title, bullets: [] } } })
            else if (next === "browser" && !v.actions) onUpdate({ visual: { type: next, actions: [{ do: "goto", url: "/" }, { do: "wait", ms: 800 }, { do: "record" }] } })
            else if (next === "terminal" && !v.command) onUpdate({ visual: { type: next, command: "npm run demo" } })
            else onUpdate({ visual: { ...v, type: next } })
          }}
        >
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {VISUAL_TYPES.map((t) => (
              <SelectItem key={t} value={t}>
                {visualLabel(t)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {v.type === "card" && (
        <CardFields
          kind={v.card?.kind ?? "title"}
          heading={v.card?.heading ?? scene.title}
          bullets={(v.card?.bullets ?? []).join("\n")}
          onChange={(patch) =>
            onUpdate({
              visual: {
                ...v,
                card: {
                  kind: patch.kind ?? v.card?.kind ?? "title",
                  heading: patch.heading ?? v.card?.heading ?? "",
                  bullets: (patch.bullets ?? v.card?.bullets ?? []),
                },
              },
            })
          }
        />
      )}

      {v.type === "browser" && (
        <ActionsEditor
          actions={v.actions ?? []}
          appUrl={project.app_url}
          onChange={(actions) => onUpdate({ visual: { ...v, actions } })}
        />
      )}

      {v.type === "terminal" && (
        <div className="space-y-2">
          <Label htmlFor="insp-cmd">Demo command (runs for real in the project folder)</Label>
          <Input
            id="insp-cmd"
            className="font-mono text-xs"
            value={v.command ?? ""}
            placeholder="npm run demo"
            onChange={(e) => onUpdate({ visual: { ...v, command: e.target.value } })}
          />
        </div>
      )}

      {(v.type === "image" || v.type === "video") && (
        <div className="space-y-2">
          <Label htmlFor="insp-asset">Asset file</Label>
          <Input
            id="insp-asset"
            className="font-mono text-xs"
            placeholder={`assets/file.${v.type === "video" ? "mp4" : "png"}`}
            value={v.path ?? ""}
            onChange={(e) => onUpdate({ visual: { ...v, path: e.target.value } })}
          />
          <Input
            type="file"
            accept={v.type === "video" ? "video/*" : "image/*"}
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) onUploadAsset(file)
            }}
          />
          <p className="text-xs text-muted-foreground">
            Optional escape hatch — browser capture and cards need no uploads.
          </p>
        </div>
      )}

      <Separator />

      <Button size="sm" variant="ghost" className="w-full text-destructive" onClick={onDelete}>
        Delete scene
      </Button>
    </div>
  )
}

/* ------------------------------------------------- field groups */

function CardFields({
  kind,
  heading,
  bullets,
  onChange,
}: {
  kind: string
  heading: string
  bullets: string
  onChange: (patch: { kind?: CardKind; heading?: string; bullets?: string[] }) => void
}) {
  return (
    <div className="space-y-2">
      <Label>Card kind</Label>
      <Select value={kind} onValueChange={(k) => k && onChange({ kind: k as CardKind })}>
        <SelectTrigger className="w-full">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="title">Title card</SelectItem>
          <SelectItem value="bullets">Bullet list</SelectItem>
          <SelectItem value="stack">Tech stack chips</SelectItem>
        </SelectContent>
      </Select>
      <Label htmlFor="insp-heading">Heading</Label>
      <Input id="insp-heading" value={heading} onChange={(e) => onChange({ heading: e.target.value })} />
      <Label htmlFor="insp-bullets">Bullets (one per line)</Label>
      <Textarea
        id="insp-bullets"
        rows={4}
        value={bullets}
        onChange={(e) => onChange({ bullets: e.target.value.split("\n").filter((l) => l.trim()) })}
      />
    </div>
  )
}

function ActionsEditor({
  actions,
  appUrl,
  onChange,
}: {
  actions: CaptureAction[]
  appUrl: string
  onChange: (actions: CaptureAction[]) => void
}) {
  const setAction = (i: number, patch: Partial<CaptureAction>) =>
    onChange(actions.map((a, idx) => (idx === i ? { ...a, ...patch } : a)))

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label>Capture steps (headless browser)</Label>
        <Button
          size="sm"
          variant="outline"
          className="h-6"
          onClick={() => onChange([...actions, { ...EMPTY_ACTION }])}
        >
          + Step
        </Button>
      </div>
      {!appUrl && (
        <p className="text-xs text-warning">Set the app URL on the Projects page before rendering.</p>
      )}
      {actions.map((a, i) => (
        <div key={i} className="space-y-1.5 rounded-md border border-border bg-card p-2">
          <div className="flex items-center gap-2">
            <span className="timecode w-5">{String(i + 1).padStart(2, "0")}</span>
            <Select value={a.do} onValueChange={(k) => k && setAction(i, { do: k as CaptureAction["do"] })}>
              <SelectTrigger className="h-7 flex-1 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ACTION_KINDS.map((k) => (
                  <SelectItem key={k} value={k}>
                    {k}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 px-2 text-destructive"
              onClick={() => onChange(actions.filter((_, idx) => idx !== i))}
            >
              ×
            </Button>
          </div>
          <ActionParams action={a} onChange={(patch) => setAction(i, patch)} />
        </div>
      ))}
      {actions.length === 0 && (
        <p className="text-xs text-muted-foreground">No steps — the scene will just hold on the page.</p>
      )}
    </div>
  )
}

function ActionParams({
  action,
  onChange,
}: {
  action: CaptureAction
  onChange: (patch: Partial<CaptureAction>) => void
}) {
  const num = (value: number | undefined, key: string) => (
    <Input
      key={key}
      type="number"
      className="h-7 text-xs"
      value={value ?? ""}
      onChange={(e) => onChange({ [key]: Number(e.target.value) } as Partial<CaptureAction>)}
    />
  )
  const text = (value: string | undefined, key: string, placeholder: string) => (
    <Input
      key={key}
      className="h-7 font-mono text-xs"
      placeholder={placeholder}
      value={value ?? ""}
      onChange={(e) => onChange({ [key]: e.target.value } as Partial<CaptureAction>)}
    />
  )
  switch (action.do) {
    case "goto":
      return text(action.url, "url", "/route-or-full-url")
    case "click":
    case "fill":
      return (
        <>
          {text(action.selector, "selector", "css selector")}
          {action.do === "fill" && text(action.text, "text", "text to type")}
        </>
      )
    case "press":
      return text(action.key, "key", "Enter")
    case "scroll":
      return num(action.delta, "delta")
    case "wait":
      return num(action.ms, "ms")
    case "record":
      return num(action.seconds, "seconds")
  }
}
