import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/AppSidebar";
import { Outlet } from "react-router-dom";
import { Activity } from "lucide-react";

export default function DashboardLayout() {
  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full bg-background">
        <AppSidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <header className="h-14 flex items-center justify-between border-b border-border bg-card/80 backdrop-blur-sm px-6 shrink-0">
            <div className="flex items-center gap-4">
              <SidebarTrigger className="text-muted-foreground hover:text-primary transition-colors" />
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded bg-primary/10 border border-primary/20 flex items-center justify-center">
                  <Activity className="w-4 h-4 text-primary" />
                </div>
                <h1 className="font-display text-sm font-bold tracking-widest">
                  JARVIS <span className="text-primary">1.5</span>
                </h1>
              </div>
              <span className="text-[10px] font-mono bg-primary/5 border border-primary/15 px-2 py-0.5 rounded text-primary/70 tracking-wider">
                v1.5.0
              </span>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 bg-jarvis-success/5 border border-jarvis-success/20 px-3 py-1 rounded">
                <div className="w-1.5 h-1.5 rounded-full bg-jarvis-success animate-pulse-dot" />
                <span className="text-[11px] font-mono text-jarvis-success tracking-wider">ONLINE</span>
              </div>
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
