import { Agent, AGENT_EMOJIS } from "@/lib/types";

interface AgentCardProps {
  agent: Agent;
  onClick?: () => void;
}

export function AgentCard({ agent, onClick }: AgentCardProps) {
  const emoji = agent.emoji || AGENT_EMOJIS[agent.slug] || '🤖';
  const statusColor = agent.status === 'active' ? 'text-jarvis-success' : agent.status === 'standby' ? 'text-jarvis-warning' : 'text-jarvis-error';

  return (
    <div
      onClick={onClick}
      className="bg-card border border-border rounded-lg p-5 transition-all hover:border-primary cursor-pointer"
    >
      <div className="flex items-center gap-3 mb-3">
        <div className="text-[28px] w-12 h-12 flex items-center justify-center bg-jarvis-elevated rounded-lg">
          {emoji}
        </div>
        <div>
          <div className="text-lg font-semibold text-foreground">{agent.name}</div>
          <div className="text-[13px] text-muted-foreground">{agent.role}</div>
        </div>
      </div>
      <div className="flex gap-2 flex-wrap mt-3">
        <span className="text-[11px] font-mono bg-jarvis-elevated border border-border px-2 py-0.5 rounded text-muted-foreground">
          Tier {agent.tier}
        </span>
        <span className="text-[11px] font-mono bg-jarvis-elevated border border-border px-2 py-0.5 rounded text-muted-foreground">
          {agent.model}
        </span>
        <span className="text-[11px] font-mono bg-jarvis-elevated border border-border px-2 py-0.5 rounded text-muted-foreground">
          {agent.team}
        </span>
        <span className={`text-xs flex items-center gap-1 ${statusColor}`}>
          ● {agent.status}
        </span>
      </div>
    </div>
  );
}
