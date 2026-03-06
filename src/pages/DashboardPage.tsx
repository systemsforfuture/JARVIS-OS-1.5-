import { useState, useEffect } from "react";
import { AGENT_DEFAULTS } from "@/lib/types";
import { api } from "@/lib/api";
import { StatCard } from "@/components/StatCard";
import { AgentCard } from "@/components/AgentCard";
import { useNavigate } from "react-router-dom";
import { Bot, CheckSquare, Brain, MessageSquare, Zap, Coins, ArrowRight } from "lucide-react";

export default function DashboardPage() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<any>(null);
  const [agents, setAgents] = useState(AGENT_DEFAULTS);

  useEffect(() => {
    api('/api/stats').then(setStats).catch(() => {});
    api('/api/agents').then(data => {
      if (Array.isArray(data) && data.length > 0) setAgents(data as any);
    }).catch(() => {});
  }, []);

  const activeAgents = agents.filter(a => a.status === 'active').length;
  const topAgents = agents.filter(a => a.status === 'active').slice(0, 6);

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="hud-card rounded-xl p-8 hud-scanline relative overflow-hidden">
        <div className="relative z-10">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-1 h-6 bg-primary rounded-full" />
            <h2 className="font-display text-xs font-bold tracking-[0.2em] text-primary">MISSION CONTROL</h2>
          </div>
          <p className="text-muted-foreground text-sm ml-3 mt-1">
            System operational · {activeAgents} Agents aktiv · Alle Systeme nominal
          </p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <StatCard 
          title="Agents" 
          value={stats?.agents?.active ?? activeAgents} 
          subtitle="aktiv" 
          colorClass="text-primary" 
          icon={<Bot className="w-4 h-4" />}
        />
        <StatCard 
          title="Tasks" 
          value={stats?.tasks?.total ?? 0} 
          subtitle={`${stats?.tasks?.completed ?? 0} erledigt`} 
          colorClass="text-jarvis-success" 
          icon={<CheckSquare className="w-4 h-4" />}
        />
        <StatCard 
          title="Learnings" 
          value={stats?.learnings ?? 0} 
          subtitle="Self-Improvement" 
          colorClass="text-jarvis-purple" 
          icon={<Brain className="w-4 h-4" />}
        />
        <StatCard 
          title="Gespräche" 
          value={stats?.conversations ?? 0} 
          subtitle="gespeichert" 
          colorClass="text-jarvis-cyan" 
          icon={<MessageSquare className="w-4 h-4" />}
        />
        <StatCard 
          title="Skills" 
          value={stats?.skills?.enabled ?? 0} 
          subtitle={`von ${stats?.skills?.total ?? 0}`} 
          colorClass="text-jarvis-gold" 
          icon={<Zap className="w-4 h-4" />}
        />
        <StatCard 
          title="Tokens" 
          value={Number(stats?.tasks?.total_tokens ?? 0).toLocaleString()} 
          subtitle={`${((stats?.tasks?.total_cost ?? 0) / 100).toFixed(2)} €`} 
          colorClass="text-primary" 
          icon={<Coins className="w-4 h-4" />}
        />
      </div>

      {/* Agent Team */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="w-1 h-5 bg-jarvis-cyan rounded-full" />
            <h3 className="font-display text-xs font-bold tracking-[0.15em] text-foreground">AGENT TEAM</h3>
          </div>
          <button 
            onClick={() => navigate('/agents')} 
            className="text-[11px] font-display tracking-wider text-muted-foreground border border-border px-3 py-1.5 rounded hover:bg-jarvis-hover hover:border-primary/30 hover:text-primary transition-all flex items-center gap-1.5"
          >
            ALLE AGENTS <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {topAgents.map(agent => (
            <AgentCard key={agent.slug} agent={agent} onClick={() => navigate('/agents')} />
          ))}
        </div>
      </div>
    </div>
  );
}
