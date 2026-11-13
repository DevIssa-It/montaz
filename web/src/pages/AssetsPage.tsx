import { useEffect, useState } from "react"
import { toast } from "sonner"

import { BrandMark } from "@/components/BrandMark"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Textarea } from "@/components/ui/textarea"
import { api } from "@/lib/api"
import type { AssetInfo, Project, Settings } from "@/types"

interface Props {
  project: Project | null
  onProjectUpdated: (p: Project) => void
  onOpenSettings: () => void
}

function formatSize(bytes: number): string {
  if (bytes > 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  return `${Math.round(bytes / 1024)} KB`
}

export function AssetsPage({ project, onProjectUpdated, onOpenSettings }: Props) {
  const [assets, setAssets] = useState<AssetInfo[] | null>(null)
  const [settings, setSettings] = useState<Settings | null>(null)
  const [prompt, setPrompt] = useState("")
  const [attachTo, setAttachTo] = useState<string>("none")
  const [generating, setGenerating] = useState(false)
  const [uploading, setUploading] = useState(false)

  const aiReady = !!(settings?.api_keys?.openai || settings?.api_keys?.gemini)

  useEffect(() => {
    void api.getSettings().then(setSettings).catch(() => {})
  }, [])

  const refresh = () => {
    if (!project) return
    void api
      .listAssets(project.id)
      .then(setAssets)
      .catch((err: Error) => toast.error(err.message))
  }

  useEffect(refresh, [project?.id]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!project) {
    return (
      <div className="mx-auto max-w-3xl p-6">
        <Card>
          <CardContent className="p-10 text-center text-sm text-muted-foreground">
            Open a project first — the asset bin belongs to each project.
          </CardContent>
        </Card>
      </div>
    )
  }

  const generate = async () => {
    if (!prompt.trim()) return
    setGenerating(true)
    try {
      const sceneId = attachTo === "none" ? undefined : attachTo
      const result = await api.generateAsset(project.id, prompt.trim(), sceneId)
      toast.success(`Asset generated: ${result.path.split("/").pop()}`)
      setPrompt("")
      refresh()
      if (result.project) onProjectUpdated(result.project)
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setGenerating(false)
    }
  }

  const upload = async (file: File) => {
    setUploading(true)
    try {
      await api.uploadAsset(project.id, file)
      toast.success(`Uploaded: ${file.name}`)
      refresh()
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Assets</h1>
        <p className="text-sm text-muted-foreground">
          The media bin for <span className="text-foreground">{project.name}</span> — uploads and
          AI-generated frames land here, ready to attach to any scene.
        </p>
      </div>

      {/* Generate with AI */}
      <Card>
        <CardContent className="space-y-4 p-5">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <span className="text-xs font-medium tracking-wider text-muted-foreground uppercase">
              Generate with AI
            </span>
            <Badge variant="outline" className="timecode">
              {settings?.api_keys?.openai ? "openai · gpt-image-1" : settings?.api_keys?.gemini ? "gemini" : "no key"}
            </Badge>
          </div>
          {!aiReady && (
            <div className="flex items-center justify-between rounded-md border border-border bg-background px-3 py-2">
              <p className="text-xs text-muted-foreground">
                Image generation needs an OpenAI or Gemini API key (your own, stored locally).
              </p>
              <Button size="sm" variant="outline" className="h-7" onClick={onOpenSettings}>
                Open Settings
              </Button>
            </div>
          )}
          <div className="space-y-2">
            <Label htmlFor="asset-prompt">Prompt</Label>
            <Textarea
              id="asset-prompt"
              rows={2}
              placeholder="e.g. flat illustration of students finding a boarding room near campus, warm colors"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
          </div>
          <div className="flex flex-wrap items-end gap-3">
            <div className="min-w-56 space-y-2">
              <Label htmlFor="asset-attach">Attach to scene (optional)</Label>
              <Select value={attachTo} onValueChange={(v) => v && setAttachTo(v)}>
                <SelectTrigger id="asset-attach" className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">— keep in bin only —</SelectItem>
                  {project.scenes.map((s, i) => (
                    <SelectItem key={s.id} value={s.id}>
                      {String(i + 1).padStart(2, "0")} · {s.title || "Untitled"}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button
              className="ml-auto"
              disabled={!aiReady || generating || !prompt.trim()}
              onClick={() => void generate()}
            >
              {generating ? "Generating… (can take ~30s)" : "Generate image"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Upload */}
      <div className="flex items-center gap-3">
        <Label htmlFor="asset-upload" className="text-sm">
          Or upload your own
        </Label>
        <Input
          id="asset-upload"
          type="file"
          accept="image/*,video/*"
          className="h-8 max-w-72 text-xs"
          disabled={uploading}
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) void upload(file)
            e.target.value = ""
          }}
        />
        {uploading && <span className="timecode">uploading…</span>}
      </div>

      {/* Bin */}
      <div className="space-y-2">
        <span className="text-xs font-medium tracking-wider text-muted-foreground uppercase">
          {assets === null ? "Loading…" : `Bin (${assets.length})`}
        </span>
        {assets === null ? (
          <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-4">
            <Skeleton className="h-40" />
            <Skeleton className="h-40" />
            <Skeleton className="h-40" />
          </div>
        ) : assets.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center gap-2 p-10 text-center">
              <BrandMark className="h-8 w-8 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                Empty bin — generate a frame above or upload one.
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {assets.map((a) => (
              <Card key={a.path} className="overflow-hidden">
                <div className="aspect-video w-full border-b border-border bg-[#090A0F]">
                  {a.kind === "image" ? (
                    <img src={a.url} alt={a.path} loading="lazy" className="h-full w-full object-cover" />
                  ) : (
                    <video src={a.url} className="h-full w-full object-cover" muted preload="metadata" />
                  )}
                </div>
                <CardContent className="space-y-1 p-3">
                  <p className="truncate font-mono text-xs text-foreground" title={a.path}>
                    {a.path.split("/").pop()}
                  </p>
                  <p className="timecode">
                    {a.kind} · {formatSize(a.size)}
                  </p>
                  <p className="timecode mt-1 text-muted-foreground/70">{a.path}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
