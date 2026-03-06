import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/AppSidebar";
import { Outlet } from "react-router-dom";

export default function DashboardLayout() {
  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <AppSidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <header className="h-16 flex items-center justify-between border-b border-border bg-card px-6 shrink-0">
            <div className="flex items-center gap-4">
              <SidebarTrigger className="text-muted-foreground" />
              <h1 className="font-display text-2xl font-bold tracking-tight">
                JARVIS <span className="text-primary">1.5</span>
              </h1>
              <span className="text-[11px] font-mono bg-jarvis-elevated border border-border px-2 py-0.5 rounded text-muted-foreground">
                v1.5.0
              </span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-jarvis-success animate-pulse-dot" />
              <span className="text-sm text-muted-foreground">Verbunden</span>
            </div>
          </header>
          <main className="flex-1 overflow-y-auto p-6">
            <Outlet />
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
