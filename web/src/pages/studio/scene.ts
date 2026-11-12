import type { ActionKind, CaptureAction, Scene, VisualType } from "@/types"

export const VISUAL_TYPES: VisualType[] = ["card", "browser", "terminal", "image", "video"]

export const ACTION_KINDS = ["goto", "click", "fill", "press", "scroll", "wait", "record"] as const satisfies readonly ActionKind[]

export const EMPTY_ACTION: CaptureAction = { do: "wait", ms: 500 }

export function newSceneDraft(index: number): Scene {
  return {
    id: `sc_${Math.random().toString(16).slice(2, 10)}`,
    title: `Scene ${index + 1}`,
    narration: "",
    visual: { type: "card", card: { kind: "title", heading: "", bullets: [] } },
    audio: null,
  }
}
