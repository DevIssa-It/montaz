import { useState } from "react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
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
import type { Project, Scene, VisualType } from "@/types"
import { ActionsEditor } from "@/pages/studio/ActionsEditor"
import { CardFields } from "@/pages/studio/CardFields"
import { VISUAL_TYPES } from "@/pages/studio/scene"

interface Props {
  scene: Scene
  project: Project
  onUpdate: (patch: Partial<Scene>) => void
  onPreviewAudio: () => void
  onUploadAsset: (file: File) => void
  previewing: boolean
  onDelete: () => void
}

/** Right-panel form for the selected scene: narration + visual configuration. */
export function Inspector({ scene, project, onUpdate, onPreviewAudio, onUploadAsset, previewing, onDelete }: Props) {
  const v = scene.visual
  const [genning, setGenning] = useState(false)

  // Turn the scene's narration into an AI frame and attach it instantly.
  const generateFromNarration = async () => {
    setGenning(true)
    try {
      const result = await api.generateAsset(project.id, scene.narration, scene.id)
      onUpdate({ visual: { type: "image", path: result.path } })
      toast.success(`AI frame attached: ${result.path.split("/").pop()}`)
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setGenning(false)
    }
  }
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
        <Button
          size="sm"
          variant="ghost"
          className="w-full"
          onClick={() => void generateFromNarration()}
          disabled={genning || !scene.narration.trim()}
          title="Generate an image from this narration with your AI key and attach it as the scene frame"
        >
          {genning ? "Generating AI frame…" : "✨ AI frame from narration"}
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
