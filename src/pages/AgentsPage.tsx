import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { AGENT_DEFAULTS, AGENT_EMOJIS } from "@/lib/types";
import type { Agent } from "@/lib/types";
import { AgentCard } from "@/components/AgentCard";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { RefreshCw } from "lucide-react";

const TEAM_ORDER = ['command', 'intelligence', 'marketing', 'sales', 'development', 'operations', 'crypto', 'customer-success'];

const TEAM_LABELS: Record<string, string> = {
  command: 'Command Center',
  intelligence: 'Intelligence',
  marketing: 'Marketing & Creative',
  sales: 'Sales & Revenue',
  development: 'Development & Infrastructure',
  operations: 'Operations & Backoffice',
  crypto: 'Crypto & Trading',
  'customer-success': 'Customer Success',
};

const TEAM_BORDER_COLORS: Record<string, string> = {
  command: 'border-primary/30',
  intelligence: 'border-jarvis-purple/30',
  marketing: 'border-jarvis-gold/30',
  sales: 'border-jarvis-success/30',
  development: 'border-jarvis-cyan/30',
  operations: 'border-muted-foreground/20',
  crypto: 'border-jarvis-warning/30',
  'customer-success': 'border-jarvis-success/30',
};

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>(AGENT_DEFAULTS);
  const [selected, setSelected] = useState<Agent | null>(null);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    api('/api/agents').then(data => {
      if (Array.isArray(data) && data.length > 0) setAgents(data as Agent[]);
    }).catch(() => {});
  }, []);

  const openDetail = async (agent: Agent) => {
    setSelected(agent);
    try {
      const s = await api(`/api/agents/${agent.slug}/stats`);
      setStats(s);
    } catch {
      setStats({ tasks: { total: 0, completed: 0 }, learning: { total: 0 }, conversations: { conversations: 0 } });
    }
  };

  const syncAll = async () => {
    try { await api('/api/agents/sync-all', { method: 'POST' }); } catch {}
  };

  // Group by team
  const teams = TEAM_ORDER
    .map(team => ({
      team,
      label: TEAM_LABELS[team] || team,
      agents: agents.filter(a => a.team === team),
      borderColor: TEAM_BORDER_COLORS[team] || 'border-border',
    }))
    .filter(t => t.agents.length > 0);

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-1 h-6 bg-jarvis-cyan rounded-full" />
          <h2 className="font-display text-xs font-bold tracking-[0.2em]">AGENT MANAGEMENT</h2>
          <span className="text-[10px] font-mono text-muted-foreground ml-2">{agents.length} Agents</span>
        </div>
        <button onClick={syncAll} className="text-[11px] font-display tracking-wider text-muted-foreground border border-border px-3 py-1.5 rounded hover:bg-jarvis-hover hover:border-primary/30 hover:text-primary transition-all flex items-center gap-1.5">
          <RefreshCw className="w-3 h-3" /> SYNC ALL
        </button>
      </div>

      {teams.map(({ team, label, agents: teamAgents, borderColor }) => (
        <div key={team}>
          <div className={`flex items-center gap-2 mb-3 pb-2 border-b ${borderColor}`}>
            <h3 className="font-display text-[10px] font-semibold tracking-[0.15em] text-muted-foreground uppercase">{label}</h3>
            <span className="text-[10px] font-mono text-muted-foreground">{teamAgents.length}</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            {teamAgents.map(agent => (
              <AgentCard key={agent.slug} agent={agent} onClick={() => openDetail(agent)} />
            ))}
          </div>
        </div>
      ))}

      <Dialog open={!!selected} onOpenChange={() => setSelected(null)}>
        <DialogContent className="max-w-[700px] bg-card border-primary/20">
          {selected && (
            <>
              <DialogHeader>
                <div className="flex items-center gap-3">
                  <div className="text-[28px] w-14 h-14 flex items-center justify-center bg-jarvis-elevated rounded-lg border border-border">
                    {selected.emoji || AGENT_EMOJIS[selected.slug] || '🤖'}
                  </div>
                  <div>
                    <DialogTitle className="font-display text-sm tracking-widest">{selected.name}</DialogTitle>
                    <p className="text-sm text-muted-foreground">{selected.role}</p>
                  </div>
                </div>
              </DialogHeader>

              <div className="grid grid-cols-3 gap-3 mt-4">
                <div className="hud-card rounded-lg p-3 text-center">
                  <div className="text-xl font-display font-bold text-primary">{stats?.tasks?.total ?? 0}</div>
                  <div className="text-[10px] font-display tracking-wider text-muted-foreground">TASKS</div>
                </div>
                <div className="hud-card rounded-lg p-3 text-center">
                  <div className="text-xl font-display font-bold text-jarvis-success">{stats?.tasks?.completed ?? 0}</div>
                  <div className="text-[10px] font-display tracking-wider text-muted-foreground">COMPLETED</div>
                </div>
                <div className="hud-card rounded-lg p-3 text-center">
                  <div className="text-xl font-display font-bold text-jarvis-purple">{stats?.learning?.total ?? 0}</div>
                  <div className="text-[10px] font-display tracking-wider text-muted-foreground">LEARNINGS</div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 mt-4">
                {[
                  { label: 'Model', value: selected.model },
                  { label: 'Tier', value: `Tier ${selected.tier}` },
                  { label: 'Team', value: selected.team },
                  { label: 'Status', value: selected.status },
                ].map(({ label, value }) => (
                  <div key={label}>
                    <label className="text-[10px] font-display tracking-wider text-muted-foreground block mb-1">{label.toUpperCase()}</label>
                    <div className="bg-jarvis-elevated border border-border rounded px-3 py-2 text-sm font-mono">{value}</div>
                  </div>
                ))}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
