import { NavLink } from "react-router-dom";
import {
  Bookmark,
  FlaskConical,
  History,
  Info,
  MessageSquarePlus,
  Search,
  Settings,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useApp } from "@/context/AppContext";
import { SystemStatus } from "@/components/system/SystemStatus";
import { Button } from "@/components/ui/button";

const NAV_ITEMS = [
  { to: "/", label: "New Research", icon: MessageSquarePlus, end: true },
  { to: "/search", label: "Search Knowledge", icon: Search, end: false },
  { to: "/history", label: "Research History", icon: History, end: false },
  { to: "/saved", label: "Saved Sources", icon: Bookmark, end: false },
  { to: "/settings", label: "Settings", icon: Settings, end: false },
  { to: "/about", label: "About", icon: Info, end: false },
];

export function Sidebar() {
  const { sidebarOpen, setSidebarOpen } = useApp();

  const content = (
    <div className="flex h-full flex-col gap-4 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-primary text-primary-foreground">
            <FlaskConical className="h-4.5 w-4.5" aria-hidden />
          </span>
          <div>
            <div className="text-sm font-semibold leading-tight">MedResearch AI</div>
            <div className="text-[10.5px] text-muted-foreground">Medical Research Assistant</div>
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden"
          aria-label="Close navigation"
          onClick={() => setSidebarOpen(false)}
        >
          <X className="h-4 w-4" aria-hidden />
        </Button>
      </div>

      <nav aria-label="Main navigation" className="flex flex-col gap-1">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={() => setSidebarOpen(false)}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium transition-colors",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
                isActive
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )
            }
          >
            <Icon className="h-4 w-4" aria-hidden />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto rounded-lg border border-border bg-card p-3">
        <SystemStatus />
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden w-60 shrink-0 border-r border-border bg-card/40 lg:block">
        {content}
      </aside>

      {/* Mobile drawer */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 lg:hidden" role="presentation">
          <div
            className="absolute inset-0 bg-black/45"
            onClick={() => setSidebarOpen(false)}
            aria-hidden
          />
          <aside className="absolute inset-y-0 left-0 w-72 border-r border-border bg-background shadow-xl animate-fade-up">
            {content}
          </aside>
        </div>
      )}
    </>
  );
}
