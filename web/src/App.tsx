import { useCallback, useEffect, useState } from "react"

import { BrandMark } from "@/components/BrandMark"
import { SplashScreen } from "@/components/SplashScreen"
import { Toaster } from "@/components/ui/sonner"
import { api } from "@/lib/api"
import { ProjectsPage } from "@/pages/ProjectsPage"
import { RenderPage } from "@/pages/RenderPage"
import { SettingsPage } from "@/pages/SettingsPage"
import { StudioPage } from "@/pages/studio/StudioPage"
import type { Project } from "@/types"

type View = "projects" | "studio" | "render" | "settings"
type BootPhase = "splash" | "fading" | "ready"

const VIEWS: { id: View; label: string }[] = [
  { id: "projects", label: "Projects" },
  { id: "studio", label: "Studio" },
  { id: "render", label: "Render" },
  { id: "settings", label: "Settings" },
]

const ACTIVE_KEY = "montaz.activeProjectId"
const BOOTED_KEY = "montaz.booted"

export default function App() {
  const [view, setView] = useState<View>("projects")
  const [projects, setProjects] = useState<Project[]>([])
  // SSOT: the active project (full object incl. scenes) lives here and is
  // passed down; pages mutate it only through onProjectUpdated.
  const [activeProjectId, setActiveProjectId] = useState<string | null>(
    () => localStorage.getItem(ACTIVE_KEY)
  )
  const [activeProject, setActiveProject] = useState<Project | null>(null)
  const [boot, setBoot] = useState<BootPhase>(() =>
    sessionStorage.getItem(BOOTED_KEY) ? "ready" : "splash"
  )

  // Show the boot splash once per session, briefly, then fade it out.
  useEffect(() => {
    if (boot === "ready") return
    const fadeTimer = setTimeout(() => setBoot("fading"), 1600)
    const doneTimer = setTimeout(() => setBoot("ready"), 2050)
    return () => {
      clearTimeout(fadeTimer)
      clearTimeout(doneTimer)
    }
  }, [boot])

  useEffect(() => {
    if (boot !== "ready") sessionStorage.setItem(BOOTED_KEY, "1")
  }, [boot])

  const refreshProjects = useCallback(() => {
    void api
      .listProjects()
      .then(setProjects)
      .catch((err: Error) => console.error(err.message))
  }, [])

  useEffect(refreshProjects, [refreshProjects])

  useEffect(() => {
    if (!activeProjectId) {
      setActiveProject(null)
      return
    }
    localStorage.setItem(ACTIVE_KEY, activeProjectId)
    void api
      .getProject(activeProjectId)
      .then(setActiveProject)
      .catch(() => {
        setActiveProject(null)
        setActiveProjectId(null)
      })
  }, [activeProjectId])

  const onProjectUpdated = useCallback((p: Project) => {
    setActiveProject(p)
    setProjects((prev) => prev.map((x) => (x.id === p.id ? p : x)))
  }, [])

  const openStudio = (id: string) => {
    setActiveProjectId(id)
    setView("studio")
  }
  const openRender = (id: string) => {
    setActiveProjectId(id)
    setView("render")
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      {boot !== "ready" && <SplashScreen fading={boot === "fading"} />}
      <header className="flex h-13 items-center gap-4 border-b border-border px-4">
        <div className="flex items-center gap-2">
          <BrandMark className="h-5 w-5 text-foreground" />
          <span className="text-sm font-semibold tracking-tight lowercase">montaz</span>
          <span className="rounded-sm border border-border px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
            local
          </span>
        </div>
        <nav className="ml-6 flex items-center gap-1">
          {VIEWS.map((v) => (
            <button
              key={v.id}
              type="button"
              onClick={() => setView(v.id)}
              className={`rounded-md px-3 py-1.5 text-sm transition-colors focus-visible:outline-2 focus-visible:outline-ring ${
                view === v.id
                  ? "bg-accent font-medium text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {v.label}
            </button>
          ))}
        </nav>
        {activeProject && (
          <div className="ml-auto flex items-center gap-2 text-xs text-muted-foreground">
            <span>active:</span>
            <span className="font-medium text-foreground">{activeProject.name}</span>
          </div>
        )}
      </header>

      <main>
        {view === "projects" && (
          <ProjectsPage
            projects={projects}
            onRefresh={refreshProjects}
            activeProjectId={activeProjectId}
            onOpenStudio={openStudio}
            onOpenRender={openRender}
          />
        )}
        {view === "studio" && <StudioPage project={activeProject} onProjectUpdated={onProjectUpdated} />}
        {view === "render" && <RenderPage project={activeProject} onProjectUpdated={onProjectUpdated} />}
        {view === "settings" && <SettingsPage />}
      </main>

      <Toaster theme="dark" position="bottom-right" richColors />
    </div>
  )
}
