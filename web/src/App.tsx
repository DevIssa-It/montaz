import { useCallback, useEffect, useState, type ReactElement } from "react"

import { BrandMark } from "@/components/BrandMark"
import { SettingsModal } from "@/components/SettingsModal"
import { SplashScreen } from "@/components/SplashScreen"
import { Toaster } from "@/components/ui/sonner"
import { api } from "@/lib/api"
import { ProjectsPage } from "@/pages/ProjectsPage"
import { RenderPage } from "@/pages/RenderPage"
import { StudioPage } from "@/pages/studio/StudioPage"
import type { Project } from "@/types"

type View = "projects" | "studio" | "render"
type BootPhase = "splash" | "fading" | "ready"

// Activity bar: icon rail, VS Code-style. Icons echo the mark's geometry.
const RAIL: { id: View; label: string; icon: ReactElement }[] = [
  {
    id: "projects",
    label: "Projects",
    icon: (
      <g>
        <rect x="3" y="4.5" width="18" height="15" rx="2" />
        <path d="M8 4.5 V19.5 M16 4.5 V19.5" />
      </g>
    ),
  },
  {
    id: "studio",
    label: "Studio",
    icon: (
      <g>
        <rect x="3" y="3" width="13" height="13" rx="2" />
        <path d="M8.5 21 H19 A2 2 0 0 0 21 19 V8.5" />
      </g>
    ),
  },
  {
    id: "render",
    label: "Render",
    icon: <path d="M13 2.5 L5.5 13.5 H11.5 L10 21.5 L18.5 9.5 H12.5 Z" />,
  },
]

const ACTIVE_KEY = "montaz.activeProjectId"
const BOOTED_KEY = "montaz.booted"
const RAIL_OPEN_KEY = "montaz.railOpen"

export default function App() {
  const [view, setView] = useState<View>("projects")
  const [projects, setProjects] = useState<Project[]>([])
  // SSOT: the active project (full object incl. scenes) lives here and is
  // passed down; pages mutate it only through onProjectUpdated.
  const [activeProjectId, setActiveProjectId] = useState<string | null>(
    () => localStorage.getItem(ACTIVE_KEY)
  )
  const [activeProject, setActiveProject] = useState<Project | null>(null)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [railOpen, setRailOpen] = useState<boolean>(
    () => localStorage.getItem(RAIL_OPEN_KEY) === "1"
  )

  const toggleRail = useCallback(() => {
    setRailOpen((prev) => {
      const next = !prev
      localStorage.setItem(RAIL_OPEN_KEY, next ? "1" : "0")
      return next
    })
  }, [])
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
    <div className="flex min-h-screen bg-background text-foreground">
      {boot !== "ready" && <SplashScreen fading={boot === "fading"} />}

      {/* Activity bar — collapsible: icons only (collapsed) or icon + label (expanded) */}
      <nav
        className={`flex shrink-0 flex-col gap-1 border-r border-border py-3 transition-[width] duration-200 ${
          railOpen ? "w-52" : "w-13"
        }`}
      >
        {RAIL.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => setView(item.id)}
            title={item.label}
            aria-current={view === item.id ? "page" : undefined}
            className={`relative flex h-10 shrink-0 items-center rounded-md transition-colors focus-visible:outline-2 focus-visible:outline-ring ${
              railOpen ? "mx-2 gap-3 px-3" : "mx-2 justify-center"
            } ${
              view === item.id
                ? "bg-accent text-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {view === item.id && (
              <span className="absolute left-0 h-5 w-0.5 rounded-full bg-primary" />
            )}
            <svg viewBox="0 0 24 24" className="h-5 w-5 shrink-0" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin={item.id === "render" ? "round" : undefined}>
              {item.icon}
            </svg>
            {railOpen && <span className="truncate text-sm">{item.label}</span>}
          </button>
        ))}

        <div className="mt-auto flex flex-col gap-1">
          <button
            type="button"
            onClick={() => setSettingsOpen(true)}
            title="Settings"
            aria-label="Settings"
            className={`flex h-10 shrink-0 items-center rounded-md text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-2 focus-visible:outline-ring ${
              railOpen ? "mx-2 gap-3 px-3" : "mx-2 justify-center"
            }`}
          >
            <svg viewBox="0 0 24 24" className="h-5 w-5 shrink-0" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
              <path d="M4 7 H14 M18 7 H20" />
              <circle cx="16" cy="7" r="2" />
              <path d="M4 17 H6 M10 17 H20" />
              <circle cx="8" cy="17" r="2" />
            </svg>
            {railOpen && <span className="truncate text-sm">Settings</span>}
          </button>
          <button
            type="button"
            onClick={toggleRail}
            title={railOpen ? "Collapse sidebar" : "Expand sidebar"}
            aria-expanded={railOpen}
            aria-label={railOpen ? "Collapse sidebar" : "Expand sidebar"}
            className="flex h-10 shrink-0 items-center rounded-md text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-2 focus-visible:outline-ring mx-2 justify-center"
          >
            <svg viewBox="0 0 24 24" className="h-5 w-5 shrink-0" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
              {railOpen ? (
                <path d="M11 17 L6 12 L11 7 M18 17 L13 12 L18 7" />
              ) : (
                <path d="M13 7 L18 12 L13 17 M6 7 L11 12 L6 17" />
              )}
            </svg>
          </button>
        </div>
      </nav>

      {/* Main column */}
      <div className="flex min-h-screen min-w-0 flex-1 flex-col">
        <header className="flex h-13 shrink-0 items-center gap-3 border-b border-border px-4">
          <div className="flex items-center gap-2">
            <BrandMark className="h-5 w-5 text-foreground" />
            <span className="text-sm font-semibold tracking-tight lowercase">montaz</span>
            <span className="rounded-sm border border-border px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
              local
            </span>
          </div>
          {activeProject && (
            <div className="ml-auto flex items-center gap-2 text-xs text-muted-foreground">
              <span>active:</span>
              <span className="font-medium text-foreground">{activeProject.name}</span>
            </div>
          )}
        </header>

        <main className="min-h-0 flex-1">
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
        </main>
      </div>

      <SettingsModal open={settingsOpen} onOpenChange={setSettingsOpen} />

      <Toaster theme="dark" position="bottom-right" richColors />
    </div>
  )
}
