import { useEffect, useState } from "react"
import { toast } from "sonner"

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
import { api } from "@/lib/api"
import type { EngineInfo, Settings, VoiceInfo } from "@/types"

const LANGUAGES = [
  { value: "en-US", label: "English (US)" },
  { value: "en-GB", label: "English (UK)" },
  { value: "id-ID", label: "Bahasa Indonesia" },
  { value: "ja-JP", label: "日本語" },
  { value: "ko-KR", label: "한국어" },
  { value: "zh-CN", label: "中文 (简体)" },
  { value: "es-ES", label: "Español" },
  { value: "fr-FR", label: "Français" },
  { value: "de-DE", label: "Deutsch" },
  { value: "pt-BR", label: "Português (BR)" },
  { value: "hi-IN", label: "हिन्दी" },
  { value: "ar-EG", label: "العربية" },
  { value: "ru-RU", label: "Русский" },
]

const KEY_FIELDS = [
  { id: "elevenlabs", label: "ElevenLabs API key", hint: "Free tier ±10 min audio/month. Most natural voices." },
  { id: "openai", label: "OpenAI API key", hint: "Unlocks OpenAI TTS voices + AI script polish." },
  { id: "gemini", label: "Gemini API key", hint: "Unlocks Gemini TTS voices + AI script polish." },
]

export function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null)
  const [engines, setEngines] = useState<EngineInfo[]>([])
  const [voices, setVoices] = useState<VoiceInfo[]>([])
  const [voiceLoading, setVoiceLoading] = useState(false)
  const [keyInputs, setKeyInputs] = useState<Record<string, string>>({})
  const [testState, setTestState] = useState<Record<string, { ok: boolean; message: string }>>({})
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    void (async () => {
      const [s, e] = await Promise.all([api.getSettings(), api.engines()])
      setSettings(s)
      setEngines(e)
    })()
  }, [])

  // Voice list follows the selected engine + language.
  useEffect(() => {
    if (!settings?.tts_engine) return
    setVoiceLoading(true)
    void api
      .voices(settings.tts_engine, settings.language)
      .then(setVoices)
      .catch((err: Error) => {
        setVoices([])
        toast.error(err.message)
      })
      .finally(() => setVoiceLoading(false))
  }, [settings?.tts_engine, settings?.language])

  if (!settings) {
    return <div className="p-6 text-sm text-muted-foreground">Loading settings…</div>
  }

  const save = async () => {
    setSaving(true)
    try {
      const keys: Record<string, string> = {}
      for (const [k, v] of Object.entries(keyInputs)) if (v.trim()) keys[k] = v.trim()
      const saved = await api.saveSettings({
        tts_engine: settings.tts_engine,
        language: settings.language,
        voice: settings.voice,
        api_keys: keys,
      })
      setSettings(saved)
      setKeyInputs({})
      toast.success("Settings saved.")
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setSaving(false)
    }
  }

  const testConnection = async (engine: string) => {
    setTestState((prev) => ({ ...prev, [engine]: { ok: true, message: "Testing…" } }))
    try {
      const result = await api.testEngine(engine)
      setTestState((prev) => ({ ...prev, [engine]: result }))
    } catch (err) {
      setTestState((prev) => ({ ...prev, [engine]: { ok: false, message: (err as Error).message } }))
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">
          The app works without any API key — Edge TTS voices are free. Keys are optional upgrades,
          stored locally in <code className="font-mono text-xs">settings.local.json</code>.
        </p>
      </div>

      {/* Voice engine */}
      <Card>
        <CardContent className="space-y-4 p-5">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <span className="text-xs font-medium tracking-wider text-muted-foreground uppercase">
              Narration voice
            </span>
            <Badge variant="outline">{engines.find((e) => e.id === settings.tts_engine)?.label ?? "—"}</Badge>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="engine">TTS engine</Label>
              <Select
                value={settings.tts_engine}
                onValueChange={(v) => v && setSettings({ ...settings, tts_engine: v, voice: "" })}
              >
                <SelectTrigger id="engine" className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {engines.map((e) => (
                    <SelectItem key={e.id} value={e.id} disabled={e.needs_key && !e.ready}>
                      {e.label}
                      {e.needs_key && !e.ready ? " — key required" : ""}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {engines
                .filter((e) => e.needs_key)
                .map((e) => (
                  <p key={e.id} className="text-xs text-muted-foreground">
                    {e.label}: {e.ready ? "key set ✓" : "no key set"}
                  </p>
                ))}
            </div>

            <div className="space-y-2">
              <Label htmlFor="language">Narration language</Label>
              <Select
                value={settings.language}
                onValueChange={(v) => v && setSettings({ ...settings, language: v, voice: "" })}
              >
                <SelectTrigger id="language" className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LANGUAGES.map((l) => (
                    <SelectItem key={l.value} value={l.value}>
                      {l.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="voice">Voice</Label>
            <Select
              value={settings.voice}
              onValueChange={(v) => v && setSettings({ ...settings, voice: v })}
              disabled={voiceLoading || voices.length === 0}
            >
              <SelectTrigger id="voice" className="w-full">
                <SelectValue placeholder={voiceLoading ? "Loading voices…" : "Pick a voice"} />
              </SelectTrigger>
              <SelectContent className="max-h-72">
                {voices.map((v) => (
                  <SelectItem key={v.id} value={v.id}>
                    {v.label}
                    <span className="text-muted-foreground"> — {v.language}</span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {voices.length === 0 && !voiceLoading && settings.tts_engine === "edge" && (
              <p className="text-xs text-muted-foreground">
                No filtered voice for this language — save, then try “All” below.
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* API keys */}
      <Card>
        <CardContent className="space-y-4 p-5">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <span className="text-xs font-medium tracking-wider text-muted-foreground uppercase">
              API keys (optional)
            </span>
            <span className="text-xs text-muted-foreground">sent only to the provider</span>
          </div>
          {KEY_FIELDS.map((f) => (
            <div key={f.id} className="grid gap-2">
              <div className="flex items-center gap-2">
                <Label htmlFor={`key-${f.id}`}>{f.label}</Label>
                {settings.api_keys[f.id] ? (
                  <Badge className="bg-primary/15 text-primary" variant="secondary">
                    set
                  </Badge>
                ) : (
                  <Badge variant="outline">unset</Badge>
                )}
                <Button
                  variant="outline"
                  size="sm"
                  className="ml-auto h-7"
                  onClick={() => void testConnection(f.id)}
                >
                  Test
                </Button>
              </div>
              <Input
                id={`key-${f.id}`}
                type="password"
                autoComplete="off"
                placeholder={settings.api_keys[f.id] ? "•••• stored — paste to replace" : "paste key…"}
                value={keyInputs[f.id] ?? ""}
                onChange={(e) => setKeyInputs((prev) => ({ ...prev, [f.id]: e.target.value }))}
              />
              <p className="text-xs text-muted-foreground">{f.hint}</p>
              {testState[f.id] && (
                <p className={`text-xs ${testState[f.id].ok ? "text-primary" : "text-destructive"}`}>
                  {testState[f.id].ok ? "✓ " : "✗ "}
                  {testState[f.id].message}
                </p>
              )}
            </div>
          ))}
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button onClick={() => void save()} disabled={saving || !settings.voice}>
          {saving ? "Saving…" : "Save settings"}
        </Button>
      </div>
    </div>
  )
}
