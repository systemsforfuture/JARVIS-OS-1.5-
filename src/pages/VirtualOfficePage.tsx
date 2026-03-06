import { useState, useEffect, useRef } from "react";
import { AGENT_DEFAULTS } from "@/lib/types";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, MessageSquare, CheckSquare, Zap } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";

/* ── Agent desk positions in the isometric world (percentage-based) ── */
const ZONES = [
  { id: 'marketing', label: 'Marketing', color: '#e74c3c', x: 18, y: 30 },
  { id: 'analytics', label: 'Analytics', color: '#2ecc71', x: 45, y: 26 },
  { id: 'development', label: 'Development', color: '#00bcd4', x: 45, y: 34 },
  { id: 'sales', label: 'Sales', color: '#f39c12', x: 32, y: 42 },
  { id: 'operations', label: 'Operations', color: '#9b59b6', x: 58, y: 42 },
  { id: 'crypto', label: 'Krypto & Trading', color: '#f1c40f', x: 75, y: 28 },
  { id: 'command', label: 'Command Center', color: '#3498db', x: 45, y: 55 },
  { id: 'customer-success', label: 'Customer Success', color: '#1abc9c', x: 65, y: 42 },
];

const DESK_POSITIONS: Record<string, { x: number; y: number; zone: string }> = {
  jarvis:  { x: 45, y: 58, zone: 'command' },
  elon:    { x: 42, y: 28, zone: 'analytics' },
  steve:   { x: 18, y: 34, zone: 'marketing' },
  iris:    { x: 25, y: 34, zone: 'marketing' },
  donald:  { x: 30, y: 46, zone: 'sales' },
  donna:   { x: 56, y: 46, zone: 'operations' },
  archi:   { x: 48, y: 36, zone: 'development' },
  satoshi: { x: 74, y: 32, zone: 'crypto' },
  felix:   { x: 63, y: 46, zone: 'customer-success' },
  andreas: { x: 70, y: 46, zone: 'customer-success' },
};

const AGENT_COLORS: Record<string, string> = {
  jarvis: '#3498db', elon: '#3498db', steve: '#e74c3c', donald: '#f39c12',
  archi: '#00bcd4', donna: '#9b59b6', iris: '#e91e8a', satoshi: '#f1c40f',
  felix: '#1abc9c', andreas: '#1abc9c',
};

const SCREEN_COLORS: Record<string, string> = {
  jarvis: '#3498db', elon: '#2ecc71', steve: '#e74c3c', donald: '#f39c12',
  archi: '#00bcd4', donna: '#9b59b6', iris: '#e91e8a', satoshi: '#f1c40f',
  felix: '#1abc9c', andreas: '#2ecc71',
};

/* ── Isometric Desk + Agent SVG ── */
function IsometricDesk({ agent, position, isSelected, onSelect, screenColor, agentColor }: {
  agent: (typeof AGENT_DEFAULTS)[0];
  position: { x: number; y: number };
  isSelected: boolean;
  onSelect: () => void;
  screenColor: string;
  agentColor: string;
}) {
  const isActive = agent.status === 'active';

  return (
    <g
      transform={`translate(${position.x}, ${position.y})`}
      onClick={onSelect}
      className="cursor-pointer"
      style={{ filter: isSelected ? `drop-shadow(0 0 8px ${agentColor})` : 'none' }}
    >
      {/* Selection ring */}
      {isSelected && (
        <ellipse cx="0" cy="18" rx="28" ry="8" fill="none" stroke={agentColor} strokeWidth="1.5" opacity="0.5">
          <animate attributeName="rx" values="28;32;28" dur="2s" repeatCount="indefinite" />
          <animate attributeName="opacity" values="0.5;0.2;0.5" dur="2s" repeatCount="indefinite" />
        </ellipse>
      )}

      {/* Desk — isometric box */}
      <polygon points="-20,10 0,0 20,10 0,20" fill="#d4d4d4" stroke="#bbb" strokeWidth="0.5" />
      <polygon points="-20,10 -20,14 0,24 0,20" fill="#c0c0c0" stroke="#bbb" strokeWidth="0.3" />
      <polygon points="20,10 20,14 0,24 0,20" fill="#aaa" stroke="#bbb" strokeWidth="0.3" />

      {/* Monitor */}
      <rect x="-8" y="-8" width="16" height="11" rx="1" fill="#1a1a2e" stroke="#333" strokeWidth="0.5" />
      <rect x="-6.5" y="-6.5" width="13" height="8" rx="0.5" fill={screenColor} opacity={isActive ? "0.85" : "0.2"}>
        {isActive && <animate attributeName="opacity" values="0.85;0.7;0.85" dur="3s" repeatCount="indefinite" />}
      </rect>
      {/* Screen content lines */}
      {isActive && (
        <>
          <line x1="-4" y1="-4" x2="4" y2="-4" stroke="rgba(255,255,255,0.4)" strokeWidth="0.5" />
          <line x1="-4" y1="-2" x2="2" y2="-2" stroke="rgba(255,255,255,0.3)" strokeWidth="0.5" />
          <line x1="-4" y1="0" x2="5" y2="0" stroke="rgba(255,255,255,0.3)" strokeWidth="0.5" />
        </>
      )}
      {/* Monitor stand */}
      <line x1="0" y1="3" x2="0" y2="6" stroke="#555" strokeWidth="1.5" />
      <line x1="-3" y1="6" x2="3" y2="6" stroke="#555" strokeWidth="1" />

      {/* Chair */}
      <ellipse cx="0" cy="22" rx="5" ry="3" fill="#2d5a27" opacity="0.7" />

      {/* Agent figure (simple stick figure) */}
      {/* Head */}
      <circle cx="0" cy="-18" r="3.5" fill="#f4c078" stroke="#d4a05a" strokeWidth="0.3" />
      {/* Body */}
      <rect x="-3" y="-14.5" width="6" height="8" rx="1.5" fill={agentColor} />
      {/* Arms */}
      <line x1="-3" y1="-12" x2="-7" y2="-7" stroke={agentColor} strokeWidth="1.5" strokeLinecap="round" />
      <line x1="3" y1="-12" x2="7" y2="-7" stroke={agentColor} strokeWidth="1.5" strokeLinecap="round" />

      {/* Name label */}
      <rect x="-14" y="-28" width="28" height="8" rx="2" fill="rgba(0,0,0,0.7)" />
      <text x="0" y="-22.5" textAnchor="middle" fill="white" fontSize="4.5" fontFamily="'Orbitron', sans-serif" fontWeight="600" letterSpacing="0.5">
        {agent.name}
      </text>

      {/* Status dot */}
      <circle cx="12" cy="-26" r="2"
        fill={agent.status === 'active' ? '#2ecc71' : agent.status === 'standby' ? '#f39c12' : '#e74c3c'}
      >
        {isActive && <animate attributeName="r" values="2;2.5;2" dur="2s" repeatCount="indefinite" />}
      </circle>

      {/* Emoji badge */}
      <text x="0" y="-31" textAnchor="middle" fontSize="6">{agent.emoji}</text>
    </g>
  );
}

/* ── Furniture pieces ── */
function Sofa({ x, y, rotation = 0 }: { x: number; y: number; rotation?: number }) {
  return (
    <g transform={`translate(${x},${y}) rotate(${rotation})`}>
      <rect x="-15" y="-5" width="30" height="10" rx="3" fill="#1a5e3a" stroke="#145a30" strokeWidth="0.5" />
      <rect x="-15" y="-8" width="30" height="4" rx="2" fill="#1e7a45" />
      <rect x="-17" y="-5" width="4" height="10" rx="2" fill="#1e7a45" />
      <rect x="13" y="-5" width="4" height="10" rx="2" fill="#1e7a45" />
    </g>
  );
}

function Plant({ x, y, size = 1 }: { x: number; y: number; size?: number }) {
  return (
    <g transform={`translate(${x},${y}) scale(${size})`}>
      <rect x="-4" y="2" width="8" height="8" rx="1" fill="#c4943d" stroke="#a67c30" strokeWidth="0.3" />
      <circle cx="0" cy="-4" r="8" fill="#27ae60" opacity="0.9" />
      <circle cx="-4" cy="-7" r="5" fill="#2ecc71" opacity="0.8" />
      <circle cx="4" cy="-6" r="5" fill="#229954" opacity="0.85" />
      <circle cx="0" cy="-9" r="4" fill="#27ae60" opacity="0.9" />
    </g>
  );
}

function CoffeeTable({ x, y }: { x: number; y: number }) {
  return (
    <g transform={`translate(${x},${y})`}>
      <polygon points="-10,0 0,-5 10,0 0,5" fill="#6d4c30" stroke="#5a3e25" strokeWidth="0.5" />
      <polygon points="-10,0 -10,2 0,7 0,5" fill="#5a3e25" />
      <polygon points="10,0 10,2 0,7 0,5" fill="#4e3420" />
      {/* Cup */}
      <circle cx="-2" cy="-1" r="1.5" fill="#fff" opacity="0.6" />
    </g>
  );
}

function FileCabinet({ x, y }: { x: number; y: number }) {
  return (
    <g transform={`translate(${x},${y})`}>
      <rect x="-5" y="-12" width="10" height="16" rx="0.5" fill="#444" stroke="#333" strokeWidth="0.5" />
      <line x1="-3" y1="-8" x2="3" y2="-8" stroke="#666" strokeWidth="0.5" />
      <line x1="-3" y1="-4" x2="3" y2="-4" stroke="#666" strokeWidth="0.5" />
      <line x1="-3" y1="0" x2="3" y2="0" stroke="#666" strokeWidth="0.5" />
      <rect x="-1" y="-10" width="2" height="1" rx="0.3" fill="#888" />
      <rect x="-1" y="-6" width="2" height="1" rx="0.3" fill="#888" />
      <rect x="-1" y="-2" width="2" height="1" rx="0.3" fill="#888" />
    </g>
  );
}

function Whiteboard({ x, y }: { x: number; y: number }) {
  return (
    <g transform={`translate(${x},${y})`}>
      <rect x="-12" y="-15" width="24" height="16" rx="1" fill="#f5f5f5" stroke="#ccc" strokeWidth="0.5" />
      {/* Post-it notes */}
      <rect x="-8" y="-12" width="5" height="4" fill="#ffeb3b" opacity="0.8" />
      <rect x="-2" y="-11" width="5" height="4" fill="#4caf50" opacity="0.7" />
      <rect x="4" y="-12" width="5" height="4" fill="#f44336" opacity="0.7" />
      <rect x="-5" y="-6" width="5" height="4" fill="#2196f3" opacity="0.7" />
      <rect x="1" y="-7" width="5" height="4" fill="#ff9800" opacity="0.8" />
    </g>
  );
}

/* ── Team Sidebar ── */
function TeamSidebar({ agents, selectedAgent, onSelect }: {
  agents: (typeof AGENT_DEFAULTS);
  selectedAgent: string | null;
  onSelect: (slug: string) => void;
}) {
  return (
    <motion.div
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      className="absolute top-16 left-4 z-20 w-44 rounded-xl overflow-hidden backdrop-blur-md"
      style={{
        background: 'rgba(255,255,255,0.92)',
        boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
      }}
    >
      <div className="p-3">
        <h3 style={{ fontFamily: "'Orbitron', sans-serif", fontSize: '11px', fontWeight: 700, letterSpacing: '0.1em', color: '#1a1a2e', marginBottom: '8px' }}>
          TEAMS
        </h3>
        <div className="space-y-1">
          {agents.map(agent => {
            const color = AGENT_COLORS[agent.slug] || '#888';
            const isSelected = selectedAgent === agent.slug;
            return (
              <button
                key={agent.slug}
                onClick={() => onSelect(agent.slug)}
                className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-left transition-all"
                style={{
                  background: isSelected ? `${color}15` : 'transparent',
                  border: isSelected ? `1px solid ${color}30` : '1px solid transparent',
                }}
              >
                <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{
                  backgroundColor: color,
                  boxShadow: agent.status === 'active' ? `0 0 6px ${color}` : 'none',
                }} />
                <span style={{ fontFamily: "'Orbitron', sans-serif", fontSize: '10px', fontWeight: 700, color: '#1a1a2e', letterSpacing: '0.05em' }}>
                  {agent.name}
                </span>
                <span style={{ fontSize: '9px', color: '#888', marginLeft: 'auto', fontFamily: "'Rajdhani', sans-serif" }}>
                  {agent.team === 'command' ? 'CEO' : agent.team === 'marketing' ? 'Marketing' : agent.team === 'sales' ? 'Sales' : agent.team === 'intelligence' ? 'Analytics' : agent.team === 'development' ? 'Dev' : agent.team === 'operations' ? 'Ops' : agent.team === 'crypto' ? 'Krypto' : 'Success'}
                </span>
              </button>
            );
          })}
        </div>
        <div className="mt-3 pt-2 border-t border-gray-200">
          <p style={{ fontSize: '8px', color: '#999', fontFamily: "'Rajdhani', sans-serif" }}>Klick = Hinspringen</p>
        </div>
      </div>
    </motion.div>
  );
}

/* ── Agent Detail Popup ── */
function AgentPopup({ agent, onClose, onNavigate }: {
  agent: (typeof AGENT_DEFAULTS)[0];
  onClose: () => void;
  onNavigate: (path: string) => void;
}) {
  const color = AGENT_COLORS[agent.slug] || '#888';
  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 10, scale: 0.95 }}
      className="absolute top-16 right-4 z-30 w-64 rounded-xl overflow-hidden"
      style={{
        background: 'linear-gradient(135deg, hsl(var(--card)), hsl(220 18% 6%))',
        border: `1px solid ${color}40`,
        boxShadow: `0 0 30px ${color}20, 0 20px 60px rgba(0,0,0,0.5)`,
      }}
    >
      <div style={{ height: '2px', background: `linear-gradient(90deg, transparent, ${color}, transparent)` }} />
      <div className="p-4">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-full flex items-center justify-center text-xl" style={{
            background: `radial-gradient(circle, ${color}40, hsl(var(--card)) 70%)`,
            border: `2px solid ${color}`,
          }}>
            {agent.emoji}
          </div>
          <div className="flex-1">
            <h3 className="font-display text-sm font-bold tracking-wider text-foreground">{agent.name}</h3>
            <p className="text-[10px] font-body text-muted-foreground">{agent.role}</p>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground text-xs">✕</button>
        </div>

        <div className="grid grid-cols-2 gap-2 mb-3">
          <div className="rounded-lg p-2 text-center" style={{ background: 'hsl(var(--jarvis-elevated))' }}>
            <div className="text-[8px] font-display text-muted-foreground tracking-wider">STATUS</div>
            <div className="text-[10px] font-display font-bold capitalize" style={{ color }}>{agent.status}</div>
          </div>
          <div className="rounded-lg p-2 text-center" style={{ background: 'hsl(var(--jarvis-elevated))' }}>
            <div className="text-[8px] font-display text-muted-foreground tracking-wider">SKILLS</div>
            <div className="text-[10px] font-display font-bold" style={{ color }}>{agent.skills.length}</div>
          </div>
        </div>

        <div className="flex flex-wrap gap-1 mb-3">
          {agent.skills.slice(0, 4).map(s => (
            <span key={s} className="text-[7px] font-mono px-1 py-0.5 rounded" style={{
              background: `${color}15`, border: `1px solid ${color}25`, color,
            }}>{s}</span>
          ))}
          {agent.skills.length > 4 && <span className="text-[7px] text-muted-foreground">+{agent.skills.length - 4}</span>}
        </div>

        <div className="flex gap-1.5">
          <button onClick={() => onNavigate('/chat')} className="flex-1 flex items-center justify-center gap-1 py-1.5 rounded text-[9px] font-display tracking-wider" style={{ background: `${color}15`, border: `1px solid ${color}25`, color }}>
            <MessageSquare className="w-3 h-3" /> CHAT
          </button>
          <button onClick={() => onNavigate('/tasks')} className="flex-1 flex items-center justify-center gap-1 py-1.5 rounded text-[9px] font-display tracking-wider" style={{ background: 'hsl(var(--jarvis-success) / 0.1)', border: '1px solid hsl(var(--jarvis-success) / 0.2)', color: 'hsl(var(--jarvis-success))' }}>
            <CheckSquare className="w-3 h-3" /> TASKS
          </button>
          <button onClick={() => onNavigate('/agents')} className="flex-1 flex items-center justify-center gap-1 py-1.5 rounded text-[9px] font-display tracking-wider" style={{ background: 'hsl(var(--jarvis-purple) / 0.1)', border: '1px solid hsl(var(--jarvis-purple) / 0.2)', color: 'hsl(var(--jarvis-purple))' }}>
            <Zap className="w-3 h-3" /> INFO
          </button>
        </div>
      </div>
    </motion.div>
  );
}

/* ── Main Page ── */
export default function VirtualOfficePage() {
  const navigate = useNavigate();
  const [agents, setAgents] = useState(AGENT_DEFAULTS);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [viewBox, setViewBox] = useState({ x: 0, y: 0, w: 1000, h: 600 });
  const svgRef = useRef<SVGSVGElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  useEffect(() => {
    api('/api/agents').then(data => {
      if (Array.isArray(data) && data.length > 0) setAgents(data as any);
    }).catch(() => {});
  }, []);

  const selected = agents.find(a => a.slug === selectedAgent);
  const activeCount = agents.filter(a => a.status === 'active').length;

  // Click agent in sidebar → center view on them
  const focusAgent = (slug: string) => {
    setSelectedAgent(slug);
    const pos = DESK_POSITIONS[slug];
    if (pos) {
      const svgX = pos.x * 10; // scale to SVG coords
      const svgY = pos.y * 10;
      setViewBox(prev => ({ ...prev, x: svgX - prev.w / 2, y: svgY - prev.h / 2 }));
    }
  };

  // Zoom with scroll
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const scale = e.deltaY > 0 ? 1.1 : 0.9;
    setViewBox(prev => {
      const newW = Math.max(400, Math.min(1600, prev.w * scale));
      const newH = Math.max(240, Math.min(960, prev.h * scale));
      return {
        x: prev.x + (prev.w - newW) / 2,
        y: prev.y + (prev.h - newH) / 2,
        w: newW, h: newH,
      };
    });
  };

  // Pan with mouse drag
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 0 || e.button === 2) {
      setIsDragging(true);
      setDragStart({ x: e.clientX, y: e.clientY });
    }
  };
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    const dx = (e.clientX - dragStart.x) * (viewBox.w / 1000);
    const dy = (e.clientY - dragStart.y) * (viewBox.h / 600);
    setViewBox(prev => ({ ...prev, x: prev.x - dx, y: prev.y - dy }));
    setDragStart({ x: e.clientX, y: e.clientY });
  };
  const handleMouseUp = () => setIsDragging(false);

  return (
    <div className="h-[calc(100vh-3.5rem)] flex flex-col -m-6">
      {/* Header bar */}
      <div className="h-12 flex items-center justify-between px-5 shrink-0" style={{
        background: 'hsl(var(--card))',
        borderBottom: '1px solid hsl(var(--border))',
      }}>
        <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-primary hover:text-primary/80 transition-colors">
          <ChevronLeft className="w-4 h-4" />
          <span className="text-sm font-body font-semibold">Zurück</span>
        </button>
        <h1 className="font-display text-sm font-bold tracking-[0.15em]">VIRTUAL OFFICE</h1>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-jarvis-success animate-pulse-dot" />
            <span className="text-xs font-display tracking-wider text-muted-foreground">{activeCount}</span>
          </div>
        </div>
      </div>

      {/* Office Canvas */}
      <div className="flex-1 relative overflow-hidden" style={{ background: 'linear-gradient(180deg, hsl(220 20% 8%), hsl(220 18% 4%))' }}>
        <TeamSidebar agents={agents} selectedAgent={selectedAgent} onSelect={focusAgent} />

        <svg
          ref={svgRef}
          viewBox={`${viewBox.x} ${viewBox.y} ${viewBox.w} ${viewBox.h}`}
          className="w-full h-full"
          style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onContextMenu={e => e.preventDefault()}
        >
          <defs>
            {/* Floor gradient */}
            <linearGradient id="floorGrad" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#1a2634" />
              <stop offset="100%" stopColor="#0f1923" />
            </linearGradient>
            {/* Carpet gradients */}
            <linearGradient id="carpetGreen" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#1a4a2e" />
              <stop offset="100%" stopColor="#0f3320" />
            </linearGradient>
            <linearGradient id="carpetDark" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#1a2634" />
              <stop offset="100%" stopColor="#0d1820" />
            </linearGradient>
            {/* Wall gradient */}
            <linearGradient id="wallGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#2a2a3e" />
              <stop offset="100%" stopColor="#1a1a2e" />
            </linearGradient>
            {/* Window light */}
            <linearGradient id="windowLight" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="rgba(255,255,255,0.15)" />
              <stop offset="100%" stopColor="rgba(255,255,255,0.02)" />
            </linearGradient>
          </defs>

          {/* ── Floor ── */}
          <rect x="-100" y="-50" width="1200" height="750" fill="url(#floorGrad)" />

          {/* Floor grid lines */}
          {[...Array(30)].map((_, i) => (
            <line key={`h${i}`} x1="-100" y1={i * 25 - 50} x2="1100" y2={i * 25 - 50} stroke="rgba(255,255,255,0.03)" strokeWidth="0.5" />
          ))}
          {[...Array(50)].map((_, i) => (
            <line key={`v${i}`} x1={i * 25 - 100} y1="-50" x2={i * 25 - 100} y2="700" stroke="rgba(255,255,255,0.03)" strokeWidth="0.5" />
          ))}

          {/* ── Back Wall ── */}
          <rect x="50" y="50" width="900" height="120" fill="url(#wallGrad)" rx="2" />
          {/* Wall panels (dark windows) */}
          {[120, 250, 380, 510, 640, 770].map(x => (
            <rect key={x} x={x} y="65" width="80" height="85" rx="2" fill="#12121e" stroke="#333" strokeWidth="0.5" />
          ))}
          {/* Window light strips */}
          <rect x="870" y="50" width="80" height="120" fill="url(#windowLight)" />

          {/* Ceiling lights */}
          {[200, 400, 600, 800].map(x => (
            <g key={x}>
              <rect x={x - 20} y="55" width="40" height="3" rx="1" fill="rgba(255,255,255,0.15)" />
              <rect x={x - 15} y="58" width="30" height="1" fill="rgba(255,255,255,0.08)" />
            </g>
          ))}

          {/* ── Carpet zones ── */}
          {/* Main green carpet */}
          <rect x="80" y="200" width="840" height="200" fill="url(#carpetGreen)" rx="3" opacity="0.6" />
          {/* Lounge carpet */}
          <rect x="200" y="450" width="400" height="120" fill="url(#carpetGreen)" rx="3" opacity="0.5" />
          {/* Side carpet */}
          <rect x="700" y="300" width="200" height="100" fill="url(#carpetDark)" rx="3" opacity="0.4" />

          {/* ── Zone labels ── */}
          {ZONES.map(zone => (
            <g key={zone.id}>
              <rect x={zone.x * 10 - 35} y={zone.y * 10 - 8} width="70" height="14" rx="3" fill="rgba(0,0,0,0.6)" />
              <circle cx={zone.x * 10 - 25} cy={zone.y * 10} r="2.5" fill={zone.color} />
              <text x={zone.x * 10 - 18} y={zone.y * 10 + 3} fill="white" fontSize="6" fontFamily="'Orbitron', sans-serif" fontWeight="600" letterSpacing="0.3">
                {zone.label}
              </text>
            </g>
          ))}

          {/* ── Wall-mounted monitors (big screens for each zone) ── */}
          {/* Marketing big screen */}
          <g transform="translate(160,100)">
            <rect x="-20" y="-15" width="40" height="25" rx="1.5" fill="#1a1a2e" stroke="#444" strokeWidth="0.5" />
            <rect x="-17" y="-12" width="34" height="19" rx="1" fill="#e74c3c" opacity="0.3" />
            <text x="0" y="0" textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="5" fontFamily="'Rajdhani', sans-serif">📊 MARKETING</text>
          </g>
          {/* Analytics big screen */}
          <g transform="translate(450,85)">
            <rect x="-25" y="-15" width="50" height="28" rx="1.5" fill="#1a1a2e" stroke="#444" strokeWidth="0.5" />
            <rect x="-22" y="-12" width="44" height="22" rx="1" fill="#00bcd4" opacity="0.3" />
            {/* Bar chart */}
            <rect x="-15" y="-2" width="4" height="8" fill="#2ecc71" opacity="0.6" />
            <rect x="-8" y="-5" width="4" height="11" fill="#2ecc71" opacity="0.7" />
            <rect x="-1" y="-8" width="4" height="14" fill="#2ecc71" opacity="0.8" />
            <rect x="6" y="-3" width="4" height="9" fill="#2ecc71" opacity="0.6" />
            <rect x="13" y="-6" width="4" height="12" fill="#2ecc71" opacity="0.7" />
          </g>
          {/* Crypto screen */}
          <g transform="translate(780,100)">
            <rect x="-18" y="-13" width="36" height="22" rx="1.5" fill="#1a1a2e" stroke="#444" strokeWidth="0.5" />
            <rect x="-15" y="-10" width="30" height="16" rx="1" fill="#f1c40f" opacity="0.2" />
            <text x="0" y="0" textAnchor="middle" fill="#f1c40f" fontSize="7" opacity="0.5">₿</text>
          </g>

          {/* ── Furniture ── */}
          {/* Lounge area */}
          <Sofa x={300} y={480} />
          <Sofa x={500} y={480} />
          <Sofa x={400} y={530} rotation={90} />
          <CoffeeTable x={400} y={490} />

          {/* Plants */}
          <Plant x={90} y={190} size={1.2} />
          <Plant x={910} y={190} size={1} />
          <Plant x={180} y={440} size={1.1} />
          <Plant x={620} y={440} size={0.9} />

          {/* Filing cabinets */}
          <FileCabinet x={80} y={350} />
          <FileCabinet x={90} y={360} />
          <FileCabinet x={100} y={370} />

          {/* Whiteboard in marketing area */}
          <Whiteboard x={130} y={280} />

          {/* ── Agent desks (render back-to-front for proper overlap) ── */}
          {agents
            .sort((a, b) => (DESK_POSITIONS[a.slug]?.y ?? 0) - (DESK_POSITIONS[b.slug]?.y ?? 0))
            .map(agent => {
              const pos = DESK_POSITIONS[agent.slug];
              if (!pos) return null;
              return (
                <IsometricDesk
                  key={agent.slug}
                  agent={agent}
                  position={{ x: pos.x * 10, y: pos.y * 10 }}
                  isSelected={selectedAgent === agent.slug}
                  onSelect={() => setSelectedAgent(prev => prev === agent.slug ? null : agent.slug)}
                  screenColor={SCREEN_COLORS[agent.slug] || '#888'}
                  agentColor={AGENT_COLORS[agent.slug] || '#888'}
                />
              );
            })}
        </svg>

        {/* Agent detail popup */}
        <AnimatePresence>
          {selected && (
            <AgentPopup
              agent={selected}
              onClose={() => setSelectedAgent(null)}
              onNavigate={path => navigate(path)}
            />
          )}
        </AnimatePresence>

        {/* Controls hint */}
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-4 px-4 py-2 rounded-full backdrop-blur-md" style={{
          background: 'rgba(255,255,255,0.06)',
          border: '1px solid rgba(255,255,255,0.08)',
        }}>
          <span className="text-[10px] text-muted-foreground font-body">🖱️ Ziehen: Bewegen</span>
          <span className="text-[10px] text-muted-foreground font-body">🔍 Scroll: Zoom</span>
          <span className="text-[10px] text-muted-foreground font-body">👆 Klick: Agent auswählen</span>
        </div>
      </div>
    </div>
  );
}
