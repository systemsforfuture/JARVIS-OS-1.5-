import { useState, useEffect } from "react";
import { AGENT_DEFAULTS } from "@/lib/types";
import { api } from "@/lib/api";
import { StatCard } from "@/components/StatCard";
import { AgentCard } from "@/components/AgentCard";
import { useNavigate } from "react-router-dom";

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

  return (
    <div>
      <h2 className="font-display text-[28px] font-semibold mb-6">Mission Control</h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-8">
        <StatCard title="Agents" value={stats?.agents?.active ?? activeAgents} subtitle="aktiv" colorClass="text-primary" />
        <StatCard title="Tasks" value={stats?.tasks?.total ?? 0} subtitle={`${stats?.tasks?.completed ?? 0} abgeschlossen`} colorClass="text-jarvis-success" />
        <StatCard title="Learnings" value={stats?.learnings ?? 0} subtitle="Self-Improvement Einträge" colorClass="text-jarvis-purple" />
        <StatCard title="Conversations" value={stats?.conversations ?? 0} subtitle="gespeichert" colorClass="text-jarvis-cyan" />
        <StatCard title="Skills" value={stats?.skills?.enabled ?? 0} subtitle={`von ${stats?.skills?.total ?? 0} aktiviert`} colorClass="text-jarvis-warning" />
        <StatCard title="Tokens" value={Number(stats?.tasks?.total_tokens ?? 0).toLocaleString()} subtitle={`${((stats?.tasks?.total_cost ?? 0) / 100).toFixed(2)} EUR Kosten`} colorClass="text-primary" />
      </div>

      <div className="flex items-center justify-between mb-4">
        <h3 className="font-display text-xl font-semibold">Agent Team</h3>
        <button onClick={() => navigate('/agents')} className="text-sm text-muted-foreground border border-border px-3 py-1.5 rounded-lg hover:bg-jarvis-hover transition-colors">
          Alle verwalten
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {agents.map(agent => (
          <AgentCard key={agent.slug} agent={agent} onClick={() => navigate('/agents')} />
        ))}
      </div>
    </div>
  );
}
