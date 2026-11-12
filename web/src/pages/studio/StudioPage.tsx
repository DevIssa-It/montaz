import { useEffect, useMemo, useRef, useState } from "react"
import { toast } from "sonner"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { api, visualLabel } from "@/lib/api"
import type { Project, Scene } from "@/types"
import { Inspector } from "@/pages/studio/Inspector"
import { PreviewCanvas } from "@/pages/studio/PreviewCanvas"
import { Timeline } from "@/pages/studio/Timeline"
import { newSceneDraft } from "@/pages/studio/scene"

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
  const [durations, setDurations] = useState<Record<string, number>>({})
  const audioRef = useRef<HTMLAudioElement | null>(null)

  // Load real narration durations (for timeline widths) once per audio file.
  useEffect(() => {
    if (!project) return
    scenes.forEach((s) => {
      if (!s.audio || durations[s.id] !== undefined) return
      const src = s.audio.startsWith("/") ? s.audio : `/api/data/${project.id}/audio/${s.audio}`
      const probe = new Audio()
      probe.preload = "metadata"
      probe.src = src
      probe.onloadedmetadata = () =>
        setDurations((prev) => (prev[s.id] === undefined ? { ...prev, [s.id]: probe.duration } : prev))
    })
  }, [project, scenes, durations])

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

  const reorder = (from: number, insertBefore: number) =>
    mutate((prev) => {
      const next = [...prev]
      const [moved] = next.splice(from, 1)
      next.splice(from < insertBefore ? insertBefore - 1 : insertBefore, 0, moved)
      return next
    })

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
      updateScene(scene.id, {
        visual: {
          ...scene.visual,
          type: file.type.startsWith("video") ? "video" : "image",
          path: result.path,
        },
      })
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
        <span className="timecode">· pipeline-first, this strip is just for review</span>
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

      {/* Review timeline — reorder convenience, the pipeline does the rest */}
      <div className="shrink-0 px-3 pb-3">
        <Timeline
          projectId={project.id}
          scenes={scenes}
          durations={durations}
          selectedId={selectedId}
          onSelect={setSelectedId}
          onReorder={reorder}
          bgmEnabled={project.bgm.enabled}
        />
      </div>
    </div>
  )
}
