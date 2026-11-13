import type { AssetInfo, EngineInfo, Project, RenderStatusInfo, Scene, Settings, VoiceInfo } from "@/types"

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(path, {
    headers: init?.body instanceof FormData ? undefined : { "Content-Type": "application/json" },
    ...init,
  })
  if (!resp.ok) {
    let detail = `HTTP ${resp.status}`
    try {
      const body = await resp.json()
      detail = body.detail || detail
    } catch {
      // non-JSON error body
    }
    throw new Error(detail)
  }
  return resp.json() as Promise<T>
}

export interface SettingsUpdate {
  tts_engine?: string
  language?: string
  voice?: string
  api_keys?: Record<string, string>
  script_polish_model?: string
}

export const api = {
  getSettings: () => request<Settings>("/api/settings"),
  saveSettings: (updates: SettingsUpdate) =>
    request<Settings>("/api/settings", { method: "PUT", body: JSON.stringify(updates) }),
  testEngine: (engine: string) =>
    request<{ ok: boolean; message: string }>(`/api/settings/test/${engine}`, { method: "POST" }),

  engines: () => request<EngineInfo[]>("/api/tts/engines"),
  voices: (engine: string, language: string) => {
    const params = new URLSearchParams({ engine })
    if (language) params.set("language", language)
    return request<VoiceInfo[]>(`/api/tts/voices?${params}`)
  },

  listProjects: () => request<Project[]>("/api/projects"),
  getProject: (id: string) => request<Project>(`/api/projects/${id}`),
  createProject: (name: string, project_folder: string, app_url: string) =>
    request<Project>("/api/projects", {
      method: "POST",
      body: JSON.stringify({ name, project_folder, app_url }),
    }),
  updateProject: (id: string, updates: Partial<Project>) =>
    request<Project>(`/api/projects/${id}`, { method: "PUT", body: JSON.stringify(updates) }),
  deleteProject: (id: string) => request<{ ok: boolean }>(`/api/projects/${id}`, { method: "DELETE" }),

  scriptgen: (id: string, language: string, polish: boolean) =>
    request<Project>(`/api/projects/${id}/scriptgen`, {
      method: "POST",
      body: JSON.stringify({ language, polish }),
    }),

  previewAudio: (id: string, sceneId: string) =>
    request<{ ok: boolean; audio: string }>(`/api/projects/${id}/audio`, {
      method: "POST",
      body: JSON.stringify({ scene_id: sceneId }),
    }),

  uploadAsset: (id: string, file: File) => {
    const form = new FormData()
    form.append("file", file)
    return request<{ ok: boolean; path: string; url: string }>(`/api/projects/${id}/assets`, {
      method: "POST",
      body: form,
    })
  },

  listAssets: (id: string) =>
    request<AssetInfo[]>(`/api/projects/${id}/assets`),

  generateAsset: (id: string, prompt: string, sceneId?: string) =>
    request<{ ok: boolean; path: string; url: string; project?: Project }>(
      `/api/projects/${id}/assets/generate`,
      { method: "POST", body: JSON.stringify({ prompt, scene_id: sceneId ?? null }) }
    ),

  render: (id: string) =>
    request<{ ok: boolean; state: string }>(`/api/projects/${id}/render`, { method: "POST" }),
  renderStatus: (id: string) => request<RenderStatusInfo>(`/api/projects/${id}/render/status`),
}

export function visualLabel(type: Scene["visual"]["type"]): string {
  switch (type) {
    case "card":
      return "Card"
    case "browser":
      return "Browser capture"
    case "terminal":
      return "Terminal"
    case "image":
      return "Image"
    case "video":
      return "Video clip"
  }
}
