export type VisualType = "card" | "browser" | "terminal" | "image" | "video"

export type CardKind = "title" | "bullets" | "stack"

export interface CardVisual {
  kind: CardKind
  heading: string
  bullets: string[]
}

export type ActionKind = "goto" | "click" | "fill" | "press" | "scroll" | "wait" | "record"

export interface CaptureAction {
  do: ActionKind
  url?: string
  selector?: string
  text?: string
  key?: string
  ms?: number
  seconds?: number
  delta?: number
}

export interface Visual {
  type: VisualType
  card?: CardVisual
  actions?: CaptureAction[]
  command?: string
  path?: string
}

export interface Scene {
  id: string
  title: string
  narration: string
  visual: Visual
  audio?: string | null
}

export interface Project {
  id: string
  name: string
  project_folder: string
  app_url: string
  tts: { engine?: string; voice?: string }
  bgm: { enabled: boolean; path: string; volume: number }
  scenes: Scene[]
  created_at: number
}

export interface Settings {
  tts_engine: string
  language: string
  voice: string
  api_keys: Record<string, boolean>
  script_polish_model: string
}

export interface EngineInfo {
  id: string
  label: string
  needs_key: boolean
  ready: boolean
}

export interface VoiceInfo {
  id: string
  label: string
  language: string
  gender: string
}

export interface RenderStatusInfo {
  state: "idle" | "running" | "done" | "error"
  progress: number
  message: string
  error?: string
  steps?: string[]
  output?: string
}
