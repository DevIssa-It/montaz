import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog"
import { SettingsPage } from "@/pages/SettingsPage"

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function SettingsModal({ open, onOpenChange }: Props) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] max-w-[calc(100%-2rem)] sm:max-w-4xl overflow-y-auto p-0">
        <DialogTitle className="sr-only">Settings</DialogTitle>
        <DialogDescription className="sr-only">
          Configure the TTS engine, voices, and API keys.
        </DialogDescription>
        <SettingsPage />
      </DialogContent>
    </Dialog>
  )
}
