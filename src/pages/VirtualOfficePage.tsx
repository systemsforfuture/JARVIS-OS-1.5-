import { useState } from "react";
import { AGENT_DEFAULTS } from "@/lib/types";
import { motion, AnimatePresence } from "framer-motion";
import { X, Zap, MessageSquare, CheckSquare } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { useEffect } from "react";

// Room positions on isometric grid — each agent gets a "desk" in the office
const ROOM_LAYOUT: Record<string, { x: number; y: number; w: number; h: number; zone: string }> = {
  jarvis:  { x: 50, y: 5,  w: 22, h: 18, zone: 'Command Center' },
  elon:    { x: 5,  y: 28, w: 18, h: 16, zone: 'Intelligence Wing' },
  steve:   { x: 27, y: 28, w: 18, h: 16, zone: 'Marketing Floor' },
  iris:    { x: 27, y: 48, w: 18, h: 16, zone: 'Marketing Floor' },
  donald:  { x: 49, y: 28, w: 18, h: 16, zone: 'Sales Floor' },
  donna:   { x: 71, y: 28, w: 18, h: 16, zone: 'Operations Hub' },
  archi:   { x: 5,  y: 48, w: 18, h: 16, zone: 'Dev Lab' },
  satoshi: { x: 71, y: 48, w: 18, h: 16, zone: 'Crypto Vault' },
  felix:   { x: 49, y: 48, w: 18, h: 16, zone: 'Customer Success' },
  andreas: { x: 49, y: 68, w: 18, h: 16, zone: 'Customer Success' },
};

const STATUS_COLORS: Record<string, string> = {
  active: 'hsl(var(--jarvis-success))',
  standby: 'hsl(var(--jarvis-warning))',
  disabled: 'hsl(var(--jarvis-error))',
};

const STATUS_GLOW: Record<string, string> = {
  active: 'hsl(160 84% 39% / 0.4)',
  standby: 'hsl(45 93% 47% / 0.3)',
  disabled: 'hsl(0 72% 51% / 0.2)',
};

const ZONE_COLORS: Record<string, string> = {
  'Command Center': 'hsl(var(--primary) / 0.06)',
  'Intelligence Wing': 'hsl(var(--jarvis-purple) / 0.05)',
  'Marketing Floor': 'hsl(var(--jarvis-gold) / 0.04)',
  'Sales Floor': 'hsl(var(--jarvis-success) / 0.04)',
  'Operations Hub': 'hsl(var(--muted-foreground) / 0.04)',
  'Dev Lab': 'hsl(var(--jarvis-cyan) / 0.05)',
  'Crypto Vault': 'hsl(var(--jarvis-warning) / 0.04)',
  'Customer Success': 'hsl(var(--jarvis-success) / 0.03)',
};

interface AgentActivity {
  slug: string;
  currentTask?: string;
  tasksToday: number;
}

function AgentRoom({
  agent,
  layout,
  activity,
  onSelect,
  isSelected,
}: {
  agent: (typeof AGENT_DEFAULTS)[0];
  layout: (typeof ROOM_LAYOUT)[string];
  activity?: AgentActivity;
  onSelect: () => void;
  isSelected: boolean;
}) {
  const statusColor = STATUS_COLORS[agent.status] || STATUS_COLORS.disabled;
  const glowColor = STATUS_GLOW[agent.status] || STATUS_GLOW.disabled;

  return (
    <motion.div
      className="absolute cursor-pointer group"
      style={{
        left: `${layout.x}%`,
        top: `${layout.y}%`,
        width: `${layout.w}%`,
        height: `${layout.h}%`,
      }}
      whileHover={{ scale: 1.03, zIndex: 20 }}
      whileTap={{ scale: 0.98 }}
      onClick={onSelect}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, delay: Math.random() * 0.3 }}
    >
      {/* Room base */}
      <div
        className="absolute inset-0 rounded-lg border transition-all duration-300"
        style={{
          background: isSelected
            ? `linear-gradient(135deg, ${ZONE_COLORS[layout.zone] || 'transparent'}, hsl(var(--primary) / 0.08))`
            : `linear-gradient(135deg, hsl(var(--card)), hsl(220 18% 8%))`,
          borderColor: isSelected ? statusColor : 'hsl(var(--border))',
          boxShadow: isSelected
            ? `0 0 30px ${glowColor}, inset 0 1px 0 hsl(var(--primary) / 0.1)`
            : `0 2px 8px hsl(0 0% 0% / 0.3)`,
        }}
      />

      {/* Isometric "3D" top edge */}
      <div
        className="absolute -top-1 left-1 right-1 h-2 rounded-t-md opacity-30"
        style={{
          background: `linear-gradient(180deg, hsl(var(--primary) / 0.15), transparent)`,
          transform: 'perspective(200px) rotateX(20deg)',
        }}
      />

      {/* Room content */}
      <div className="relative z-10 h-full flex flex-col items-center justify-center p-2 gap-1">
        {/* Agent avatar with status ring */}
        <div className="relative">
          <motion.div
            className="w-10 h-10 sm:w-12 sm:h-12 rounded-full flex items-center justify-center text-lg sm:text-xl"
            style={{
              background: `radial-gradient(circle at 40% 35%, ${glowColor}, hsl(var(--card)) 70%)`,
              border: `2px solid ${statusColor}`,
              boxShadow: agent.status === 'active'
                ? `0 0 15px ${glowColor}`
                : 'none',
            }}
            animate={agent.status === 'active' ? {
              boxShadow: [
                `0 0 10px ${glowColor}`,
                `0 0 25px ${glowColor}`,
                `0 0 10px ${glowColor}`,
              ],
            } : {}}
            transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }}
          >
            {agent.emoji}
          </motion.div>

          {/* Status indicator */}
          <motion.div
            className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2"
            style={{
              backgroundColor: statusColor,
              borderColor: 'hsl(var(--card))',
            }}
            animate={agent.status === 'active' ? { scale: [1, 1.3, 1] } : {}}
            transition={{ duration: 2, repeat: Infinity }}
          />
        </div>

        {/* Name */}
        <span className="font-display text-[8px] sm:text-[9px] font-bold tracking-[0.15em] text-foreground/90 truncate max-w-full">
          {agent.name}
        </span>

        {/* Current task preview */}
        <span className="text-[7px] sm:text-[8px] font-body text-muted-foreground/60 truncate max-w-full text-center leading-tight">
          {activity?.currentTask || agent.role}
        </span>
      </div>

      {/* Hover overlay */}
      <div className="absolute inset-0 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none"
        style={{
          background: `linear-gradient(135deg, ${glowColor}, transparent)`,
        }}
      />

      {/* Connection lines to JARVIS (only for non-jarvis) */}
      {agent.slug !== 'jarvis' && (
        <svg className="absolute pointer-events-none opacity-20 group-hover:opacity-50 transition-opacity" style={{
          left: '50%', top: '-50%', width: '1px', height: '50%',
          overflow: 'visible',
        }}>
          <line x1="0" y1="100%" x2="0" y2="0" stroke="hsl(var(--primary))" strokeWidth="1" strokeDasharray="3 3">
            <animate attributeName="stroke-dashoffset" from="0" to="-12" dur="2s" repeatCount="indefinite" />
          </line>
        </svg>
      )}
    </motion.div>
  );
}

function AgentDetailPanel({
  agent,
  activity,
  onClose,
  onNavigate,
}: {
  agent: (typeof AGENT_DEFAULTS)[0];
  activity?: AgentActivity;
  onClose: () => void;
  onNavigate: (path: string) => void;
}) {
  const layout = ROOM_LAYOUT[agent.slug];
  return (
    <motion.div
      initial={{ opacity: 0, x: 30 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 30 }}
      className="absolute top-4 right-4 w-72 z-30 rounded-xl overflow-hidden"
      style={{
        background: 'linear-gradient(135deg, hsl(var(--card)), hsl(220 18% 6%))',
        border: '1px solid hsl(var(--primary) / 0.2)',
        boxShadow: '0 0 40px hsl(var(--primary) / 0.1), 0 20px 60px hsl(0 0% 0% / 0.5)',
      }}
    >
      {/* Top glow line */}
      <div className="h-[1px] w-full" style={{ background: 'linear-gradient(90deg, transparent, hsl(var(--primary) / 0.5), transparent)' }} />

      <div className="p-5">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full flex items-center justify-center text-2xl"
              style={{
                background: `radial-gradient(circle, ${STATUS_GLOW[agent.status]}, hsl(var(--card)) 70%)`,
                border: `2px solid ${STATUS_COLORS[agent.status]}`,
              }}
            >
              {agent.emoji}
            </div>
            <div>
              <h3 className="font-display text-sm font-bold tracking-wider">{agent.name}</h3>
              <p className="text-[10px] font-body text-muted-foreground">{agent.role}</p>
            </div>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Zone */}
        <div className="flex items-center gap-2 mb-4">
          <div className="w-1 h-3 rounded-full bg-primary" />
          <span className="text-[9px] font-display tracking-[0.15em] text-primary">{layout?.zone}</span>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-2 mb-4">
          <div className="rounded-lg p-2 text-center" style={{ background: 'hsl(var(--jarvis-elevated))' }}>
            <div className="text-[9px] font-display text-muted-foreground tracking-wider">STATUS</div>
            <div className="text-xs font-display font-bold capitalize" style={{ color: STATUS_COLORS[agent.status] }}>
              {agent.status}
            </div>
          </div>
          <div className="rounded-lg p-2 text-center" style={{ background: 'hsl(var(--jarvis-elevated))' }}>
            <div className="text-[9px] font-display text-muted-foreground tracking-wider">SKILLS</div>
            <div className="text-xs font-display font-bold text-primary">{agent.skills.length}</div>
          </div>
          <div className="rounded-lg p-2 text-center" style={{ background: 'hsl(var(--jarvis-elevated))' }}>
            <div className="text-[9px] font-display text-muted-foreground tracking-wider">TASKS</div>
            <div className="text-xs font-display font-bold text-jarvis-success">{activity?.tasksToday ?? 0}</div>
          </div>
        </div>

        {/* Current task */}
        {activity?.currentTask && (
          <div className="rounded-lg p-3 mb-4" style={{ background: 'hsl(var(--jarvis-elevated))', border: '1px solid hsl(var(--border))' }}>
            <div className="text-[9px] font-display tracking-wider text-muted-foreground mb-1">CURRENT TASK</div>
            <p className="text-xs font-body text-foreground/80">{activity.currentTask}</p>
          </div>
        )}

        {/* Skills preview */}
        <div className="mb-4">
          <div className="text-[9px] font-display tracking-wider text-muted-foreground mb-2">SKILLS</div>
          <div className="flex flex-wrap gap-1">
            {agent.skills.slice(0, 6).map(s => (
              <span key={s} className="text-[8px] font-mono px-1.5 py-0.5 rounded" style={{
                background: 'hsl(var(--primary) / 0.08)',
                border: '1px solid hsl(var(--primary) / 0.15)',
                color: 'hsl(var(--primary))',
              }}>
                {s}
              </span>
            ))}
            {agent.skills.length > 6 && (
              <span className="text-[8px] font-mono text-muted-foreground">+{agent.skills.length - 6}</span>
            )}
          </div>
        </div>

        {/* Quick actions */}
        <div className="flex gap-2">
          <button
            onClick={() => onNavigate('/chat')}
            className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-[10px] font-display tracking-wider transition-all hover:bg-primary/20"
            style={{ background: 'hsl(var(--primary) / 0.1)', border: '1px solid hsl(var(--primary) / 0.2)', color: 'hsl(var(--primary))' }}
          >
            <MessageSquare className="w-3 h-3" /> CHAT
          </button>
          <button
            onClick={() => onNavigate('/tasks')}
            className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-[10px] font-display tracking-wider transition-all hover:bg-jarvis-success/20"
            style={{ background: 'hsl(var(--jarvis-success) / 0.1)', border: '1px solid hsl(var(--jarvis-success) / 0.2)', color: 'hsl(var(--jarvis-success))' }}
          >
            <CheckSquare className="w-3 h-3" /> TASKS
          </button>
          <button
            onClick={() => onNavigate('/agents')}
            className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-[10px] font-display tracking-wider transition-all hover:bg-jarvis-purple/20"
            style={{ background: 'hsl(var(--jarvis-purple) / 0.1)', border: '1px solid hsl(var(--jarvis-purple) / 0.2)', color: 'hsl(var(--jarvis-purple))' }}
          >
            <Zap className="w-3 h-3" /> DETAILS
          </button>
        </div>
      </div>
    </motion.div>
  );
}

export default function VirtualOfficePage() {
  const navigate = useNavigate();
  const [agents, setAgents] = useState(AGENT_DEFAULTS);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [activities, setActivities] = useState<Record<string, AgentActivity>>({});

  useEffect(() => {
    // Try to load real agent data
    api('/api/agents').then(data => {
      if (Array.isArray(data) && data.length > 0) setAgents(data as any);
    }).catch(() => {});

    // Try to load recent tasks for activity
    api('/api/tasks?limit=50').then(data => {
      if (Array.isArray(data) && data.length > 0) {
        const acts: Record<string, AgentActivity> = {};
        data.forEach((t: any) => {
          const slug = t.agent_slug || 'jarvis';
          if (!acts[slug]) acts[slug] = { slug, tasksToday: 0 };
          acts[slug].tasksToday++;
          if (t.status === 'in_progress' && !acts[slug].currentTask) {
            acts[slug].currentTask = t.title;
          }
        });
        setActivities(acts);
      }
    }).catch(() => {});
  }, []);

  const selected = agents.find(a => a.slug === selectedAgent);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-1 h-5 bg-primary rounded-full" />
          <h2 className="font-display text-[10px] font-bold tracking-[0.2em] text-primary">VIRTUAL OFFICE</h2>
          <span className="text-[9px] font-mono text-muted-foreground/50 ml-2">{agents.filter(a => a.status === 'active').length} AGENTS ONLINE</span>
        </div>
        <div className="flex items-center gap-2">
          {['active', 'standby', 'disabled'].map(status => (
            <div key={status} className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: STATUS_COLORS[status] }} />
              <span className="text-[9px] font-display tracking-wider text-muted-foreground capitalize">{status}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Office Floor Plan */}
      <div className="flex-1 relative rounded-xl overflow-hidden min-h-[500px]" style={{
        background: 'linear-gradient(135deg, hsl(220 20% 3%), hsl(220 18% 6%))',
        border: '1px solid hsl(var(--border))',
      }}>
        {/* Grid pattern */}
        <div className="absolute inset-0 opacity-[0.03]" style={{
          backgroundImage: `
            linear-gradient(hsl(var(--primary)) 1px, transparent 1px),
            linear-gradient(90deg, hsl(var(--primary)) 1px, transparent 1px)
          `,
          backgroundSize: '30px 30px',
        }} />

        {/* Diagonal isometric lines for depth */}
        <svg className="absolute inset-0 w-full h-full opacity-[0.02] pointer-events-none">
          {[...Array(20)].map((_, i) => (
            <line key={i} x1={`${i * 10}%`} y1="0" x2={`${i * 10 - 30}%`} y2="100%" stroke="hsl(var(--primary))" strokeWidth="0.5" />
          ))}
        </svg>

        {/* Zone labels */}
        {Object.entries(
          agents.reduce((acc, a) => {
            const zone = ROOM_LAYOUT[a.slug]?.zone;
            if (zone && !acc[zone]) acc[zone] = ROOM_LAYOUT[a.slug];
            return acc;
          }, {} as Record<string, typeof ROOM_LAYOUT[string]>)
        ).map(([zone, layout]) => (
          <div
            key={zone}
            className="absolute text-[7px] sm:text-[8px] font-display tracking-[0.2em] text-muted-foreground/25 pointer-events-none"
            style={{ left: `${layout.x}%`, top: `${layout.y - 3}%` }}
          >
            {zone.toUpperCase()}
          </div>
        ))}

        {/* Agent Rooms */}
        {agents.map(agent => {
          const layout = ROOM_LAYOUT[agent.slug];
          if (!layout) return null;
          return (
            <AgentRoom
              key={agent.slug}
              agent={agent}
              layout={layout}
              activity={activities[agent.slug]}
              isSelected={selectedAgent === agent.slug}
              onSelect={() => setSelectedAgent(prev => prev === agent.slug ? null : agent.slug)}
            />
          );
        })}

        {/* Central JARVIS energy core — connecting lines */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 5 }}>
          {agents.filter(a => a.slug !== 'jarvis').map(agent => {
            const from = ROOM_LAYOUT.jarvis;
            const to = ROOM_LAYOUT[agent.slug];
            if (!from || !to) return null;
            const x1 = from.x + from.w / 2;
            const y1 = from.y + from.h;
            const x2 = to.x + to.w / 2;
            const y2 = to.y;
            return (
              <line
                key={agent.slug}
                x1={`${x1}%`} y1={`${y1}%`}
                x2={`${x2}%`} y2={`${y2}%`}
                stroke={STATUS_COLORS[agent.status]}
                strokeWidth="0.5"
                strokeDasharray="4 4"
                opacity={selectedAgent === agent.slug ? 0.6 : 0.1}
                className="transition-opacity duration-300"
              >
                <animate attributeName="stroke-dashoffset" from="0" to="-16" dur="3s" repeatCount="indefinite" />
              </line>
            );
          })}
        </svg>

        {/* Detail Panel */}
        <AnimatePresence>
          {selected && (
            <AgentDetailPanel
              agent={selected}
              activity={activities[selected.slug]}
              onClose={() => setSelectedAgent(null)}
              onNavigate={(path) => navigate(path)}
            />
          )}
        </AnimatePresence>

        {/* Floor scan effect */}
        <motion.div
          className="absolute inset-x-0 h-[2px] pointer-events-none"
          style={{
            background: 'linear-gradient(90deg, transparent, hsl(var(--primary) / 0.15), transparent)',
            zIndex: 1,
          }}
          animate={{ top: ['0%', '100%'] }}
          transition={{ duration: 6, repeat: Infinity, ease: "linear" }}
        />
      </div>
    </div>
  );
}
