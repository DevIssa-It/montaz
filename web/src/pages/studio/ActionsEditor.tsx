import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { CaptureAction } from "@/types"
import { ActionParams } from "@/pages/studio/ActionParams"
import { ACTION_KINDS, EMPTY_ACTION } from "@/pages/studio/scene"

interface Props {
  actions: CaptureAction[]
  appUrl: string
  onChange: (actions: CaptureAction[]) => void
}

export function ActionsEditor({ actions, appUrl, onChange }: Props) {
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
