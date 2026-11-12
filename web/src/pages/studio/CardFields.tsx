import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import type { CardKind } from "@/types"

interface Props {
  kind: CardKind
  heading: string
  bullets: string
  onChange: (patch: { kind?: CardKind; heading?: string; bullets?: string[] }) => void
}

export function CardFields({ kind, heading, bullets, onChange }: Props) {
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
