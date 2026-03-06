import { Agent, AGENT_EMOJIS } from "@/lib/types";

interface AgentCardProps {
  agent: Agent;
  onClick?: () => void;
  compact?: boolean;
}

const TEAM_COLORS: Record<string, string> = {
  command: 'border-primary/30 bg-primary/5',
  intelligence: 'border-jarvis-purple/30 bg-jarvis-purple/5',
  marketing: 'border-jarvis-gold/30 bg-jarvis-gold/5',
  sales: 'border-jarvis-success/30 bg-jarvis-success/5',
  development: 'border-jarvis-cyan/30 bg-jarvis-cyan/5',
  operations: 'border-muted-foreground/30 bg-muted-foreground/5',
  crypto: 'border-jarvis-warning/30 bg-jarvis-warning/5',
  'customer-success': 'border-jarvis-success/30 bg-jarvis-success/5',
};

const TEAM_TEXT_COLORS: Record<string, string> = {
  command: 'text-primary',
  intelligence: 'text-jarvis-purple',
  marketing: 'text-jarvis-gold',
  sales: 'text-jarvis-success',
  development: 'text-jarvis-cyan',
  operations: 'text-muted-foreground',
  crypto: 'text-jarvis-warning',
  'customer-success': 'text-jarvis-success',
};

export function AgentCard({ agent, onClick, compact }: AgentCardProps) {
  const emoji = agent.emoji || AGENT_EMOJIS[agent.slug] || '🤖';
  const statusColor = agent.status === 'active' ? 'bg-jarvis-success' : agent.status === 'standby' ? 'bg-jarvis-warning' : 'bg-jarvis-error';
  const teamColor = TEAM_COLORS[agent.team] || 'border-border bg-secondary';
  const teamTextColor = TEAM_TEXT_COLORS[agent.team] || 'text-muted-foreground';

  if (compact) {
    return (
      <div onClick={onClick} className="hud-card rounded-lg p-3 cursor-pointer hover:hud-glow transition-all flex items-center gap-3">
        <div className="text-xl w-9 h-9 flex items-center justify-center bg-jarvis-elevated rounded border border-border">
          {emoji}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-display font-semibold tracking-wider">{agent.name}</div>
          <div className="text-[11px] text-muted-foreground truncate">{agent.role}</div>
        </div>
        <div className={`w-2 h-2 rounded-full ${statusColor}`} />
      </div>
    );
  }

  return (
    <div
      onClick={onClick}
      className="hud-card rounded-lg p-5 transition-all hover:hud-glow cursor-pointer group"
    >
      <div className="flex items-center gap-3 mb-4">
        <div className="text-2xl w-12 h-12 flex items-center justify-center bg-jarvis-elevated rounded-lg border border-border group-hover:border-primary/30 transition-colors">
          {emoji}
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <div className="font-display text-sm font-bold tracking-wider">{agent.name}</div>
            <div className={`w-1.5 h-1.5 rounded-full ${statusColor}`} />
          </div>
          <div className="text-[12px] text-muted-foreground">{agent.role}</div>
        </div>
      </div>
      <div className="flex gap-2 flex-wrap">
        <span className={`text-[10px] font-display font-semibold tracking-wider px-2 py-0.5 rounded border ${teamColor} ${teamTextColor}`}>
          {agent.team.toUpperCase()}
        </span>
        <span className="text-[10px] font-mono bg-jarvis-elevated border border-border px-2 py-0.5 rounded text-muted-foreground">
          T{agent.tier}
        </span>
        <span className="text-[10px] font-mono bg-jarvis-elevated border border-border px-2 py-0.5 rounded text-muted-foreground">
          {agent.model}
        </span>
      </div>
    </div>
  );
}
