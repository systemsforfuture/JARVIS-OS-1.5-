import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { AGENT_DEFAULTS, AGENT_EMOJIS } from "@/lib/types";
import type { Agent } from "@/lib/types";
import { AgentCard } from "@/components/AgentCard";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

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
    try {
      await api('/api/agents/sync-all', { method: 'POST' });
    } catch {}
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <div>
          <h2 className="font-display text-[28px] font-semibold">Agent Management</h2>
          <p className="text-sm text-muted-foreground -mt-1 mb-6">Agents konfigurieren und zu OpenClaw synchronisieren</p>
        </div>
        <button onClick={syncAll} className="text-sm text-muted-foreground border border-border px-3 py-1.5 rounded-lg hover:bg-jarvis-hover transition-colors">
          Alle zu OpenClaw sync
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {agents.map(agent => (
          <AgentCard key={agent.slug} agent={agent} onClick={() => openDetail(agent)} />
        ))}
      </div>

      <Dialog open={!!selected} onOpenChange={() => setSelected(null)}>
        <DialogContent className="max-w-[700px] bg-card border-border">
          {selected && (
            <>
              <DialogHeader>
                <div className="flex items-center gap-3">
                  <div className="text-[32px] w-14 h-14 flex items-center justify-center bg-jarvis-elevated rounded-lg">
                    {selected.emoji || AGENT_EMOJIS[selected.slug] || '🤖'}
                  </div>
                  <div>
                    <DialogTitle className="font-display text-2xl">{selected.name}</DialogTitle>
                    <p className="text-sm text-muted-foreground">{selected.role}</p>
                  </div>
                </div>
              </DialogHeader>

              <div className="grid grid-cols-3 gap-3 mt-4">
                <div className="bg-jarvis-elevated rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold font-mono text-primary">{stats?.tasks?.total ?? 0}</div>
                  <div className="text-xs text-muted-foreground">Tasks</div>
                </div>
                <div className="bg-jarvis-elevated rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold font-mono text-jarvis-success">{stats?.tasks?.completed ?? 0}</div>
                  <div className="text-xs text-muted-foreground">Completed</div>
                </div>
                <div className="bg-jarvis-elevated rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold font-mono text-jarvis-purple">{stats?.learning?.total ?? 0}</div>
                  <div className="text-xs text-muted-foreground">Learnings</div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mt-4">
                <div>
                  <label className="text-[13px] text-muted-foreground block mb-1">Model</label>
                  <div className="bg-jarvis-elevated border border-border rounded-lg px-3 py-2 text-sm font-mono">{selected.model}</div>
                </div>
                <div>
                  <label className="text-[13px] text-muted-foreground block mb-1">Tier</label>
                  <div className="bg-jarvis-elevated border border-border rounded-lg px-3 py-2 text-sm font-mono">Tier {selected.tier}</div>
                </div>
                <div>
                  <label className="text-[13px] text-muted-foreground block mb-1">Team</label>
                  <div className="bg-jarvis-elevated border border-border rounded-lg px-3 py-2 text-sm font-mono">{selected.team}</div>
                </div>
                <div>
                  <label className="text-[13px] text-muted-foreground block mb-1">Status</label>
                  <div className="bg-jarvis-elevated border border-border rounded-lg px-3 py-2 text-sm font-mono">{selected.status}</div>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
