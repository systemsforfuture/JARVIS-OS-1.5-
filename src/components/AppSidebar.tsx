import {
  BarChart3, MessageSquare, CheckSquare, Bot, Zap, Brain,
  BookOpen, FileText, Mic, Monitor, Rocket, Settings
} from "lucide-react";
import { NavLink } from "@/components/NavLink";
import {
  Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent,
  SidebarGroupLabel, SidebarMenu, SidebarMenuButton, SidebarMenuItem, useSidebar,
} from "@/components/ui/sidebar";

const navGroups = [
  {
    label: "Command Center",
    items: [
      { title: "Dashboard", url: "/", icon: BarChart3 },
      { title: "Chat", url: "/chat", icon: MessageSquare },
      { title: "Tasks", url: "/tasks", icon: CheckSquare },
    ],
  },
  {
    label: "Team",
    items: [
      { title: "Agents", url: "/agents", icon: Bot },
      { title: "Skills", url: "/skills", icon: Zap },
    ],
  },
  {
    label: "Intelligence",
    items: [
      { title: "Memory", url: "/memory", icon: Brain },
      { title: "Learning", url: "/learning", icon: BookOpen },
      { title: "Conversations", url: "/conversations", icon: FileText },
    ],
  },
  {
    label: "Wearable",
    items: [
      { title: "OMI Device", url: "/omi", icon: Mic },
    ],
  },
  {
    label: "System",
    items: [
      { title: "Services", url: "/services", icon: Monitor },
      { title: "Setup Wizard", url: "/onboarding", icon: Rocket },
      { title: "Settings", url: "/settings", icon: Settings },
    ],
  },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const collapsed = state === "collapsed";

  return (
    <Sidebar collapsible="icon">
      <SidebarContent>
        {navGroups.map((group) => (
          <SidebarGroup key={group.label}>
            <SidebarGroupLabel className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              {group.label}
            </SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {group.items.map((item) => (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton asChild>
                      <NavLink
                        to={item.url}
                        end={item.url === "/"}
                        className="hover:bg-jarvis-hover"
                        activeClassName="bg-jarvis-elevated text-foreground border border-border"
                      >
                        <item.icon className="mr-2 h-4 w-4" />
                        {!collapsed && <span>{item.title}</span>}
                      </NavLink>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>
    </Sidebar>
  );
}
