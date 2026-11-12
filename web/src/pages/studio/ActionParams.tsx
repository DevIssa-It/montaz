import { Input } from "@/components/ui/input"
import type { CaptureAction } from "@/types"

/** Parameter inputs for one capture step; shape follows the action kind. */
export function ActionParams({
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
